"""
Event System - Decoupled communication for modular architecture
Implements event-driven patterns for loose coupling between components
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import weakref
import inspect


class EventPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    type: str
    payload: Any
    source: str
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventSubscription:
    handler: Callable
    event_type: str
    priority: EventPriority
    once: bool = False
    filter_func: Optional[Callable[[Event], bool]] = None
    weak_ref: bool = False


class EventManager:
    """Advanced event management system with filtering, priorities, and lifecycle management"""
    
    def __init__(self):
        self._subscriptions: Dict[str, List[EventSubscription]] = {}
        self._wildcard_subscriptions: List[EventSubscription] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._logger = logging.getLogger(f"{__name__}.EventManager")
        self._stats = {
            "events_emitted": 0,
            "events_handled": 0,
            "errors": 0
        }
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
        filter_func: Optional[Callable[[Event], bool]] = None,
        weak_ref: bool = False
    ) -> str:
        """
        Subscribe to events with advanced options
        
        Args:
            event_type: Event type to subscribe to (supports wildcards with *)
            handler: Function to call when event occurs  
            priority: Priority level for handler execution order
            once: If True, handler is removed after first execution
            filter_func: Optional function to filter events before handling
            weak_ref: Use weak reference to handler (prevents memory leaks)
        
        Returns:
            Subscription ID for later unsubscription
        """
        subscription = EventSubscription(
            handler=weakref.WeakMethod(handler) if weak_ref and hasattr(handler, '__self__') else handler,
            event_type=event_type,
            priority=priority,
            once=once,
            filter_func=filter_func,
            weak_ref=weak_ref
        )
        
        # Handle wildcard subscriptions
        if '*' in event_type:
            self._wildcard_subscriptions.append(subscription)
        else:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            self._subscriptions[event_type].append(subscription)
        
        # Sort by priority
        self._sort_subscriptions(event_type)
        
        subscription_id = f"{event_type}_{id(subscription)}"
        self._logger.debug(f"Subscribed to {event_type} with priority {priority.name}")
        
        return subscription_id
    
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """Unsubscribe a handler from an event type"""
        removed = False
        
        # Check regular subscriptions
        if event_type in self._subscriptions:
            original_length = len(self._subscriptions[event_type])
            self._subscriptions[event_type] = [
                sub for sub in self._subscriptions[event_type]
                if not self._is_same_handler(sub.handler, handler)
            ]
            removed = len(self._subscriptions[event_type]) < original_length
        
        # Check wildcard subscriptions
        if '*' in event_type:
            original_length = len(self._wildcard_subscriptions)
            self._wildcard_subscriptions = [
                sub for sub in self._wildcard_subscriptions
                if not (sub.event_type == event_type and self._is_same_handler(sub.handler, handler))
            ]
            removed = removed or len(self._wildcard_subscriptions) < original_length
        
        if removed:
            self._logger.debug(f"Unsubscribed from {event_type}")
        
        return removed
    
    async def emit(
        self,
        event_type: str,
        payload: Any = None,
        source: str = "system",
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Emit an event to all matching subscribers
        
        Returns:
            Number of handlers that processed the event
        """
        event = Event(
            type=event_type,
            payload=payload,
            source=source,
            priority=priority,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        # Add to history
        self._add_to_history(event)
        
        # Get all matching subscriptions
        subscriptions = self._get_matching_subscriptions(event_type)
        
        # Filter subscriptions based on their filter functions
        filtered_subscriptions = []
        for subscription in subscriptions:
            if subscription.filter_func is None or subscription.filter_func(event):
                filtered_subscriptions.append(subscription)
        
        # Sort by priority
        filtered_subscriptions.sort(key=lambda s: s.priority.value, reverse=True)
        
        self._logger.debug(f"Emitting {event_type} to {len(filtered_subscriptions)} handlers")
        
        # Execute handlers
        handlers_executed = 0
        subscriptions_to_remove = []
        
        for subscription in filtered_subscriptions:
            try:
                handler = subscription.handler
                
                # Handle weak references
                if subscription.weak_ref and isinstance(handler, weakref.WeakMethod):
                    handler = handler()
                    if handler is None:
                        subscriptions_to_remove.append(subscription)
                        continue
                
                # Execute handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                
                handlers_executed += 1
                self._stats["events_handled"] += 1
                
                # Remove one-time subscriptions
                if subscription.once:
                    subscriptions_to_remove.append(subscription)
            
            except Exception as e:
                self._logger.error(f"Error in event handler for {event_type}: {e}")
                self._stats["errors"] += 1
        
        # Clean up subscriptions
        for subscription in subscriptions_to_remove:
            self._remove_subscription(subscription)
        
        self._stats["events_emitted"] += 1
        return handlers_executed
    
    async def emit_and_wait(
        self,
        event_type: str,
        payload: Any = None,
        source: str = "system",
        timeout: float = 30.0,
        correlation_id: Optional[str] = None
    ) -> List[Any]:
        """
        Emit event and collect results from all handlers
        """
        results = []
        subscriptions = self._get_matching_subscriptions(event_type)
        
        event = Event(
            type=event_type,
            payload=payload,
            source=source,
            correlation_id=correlation_id
        )
        
        # Execute all handlers and collect results
        tasks = []
        for subscription in subscriptions:
            if subscription.filter_func is None or subscription.filter_func(event):
                handler = subscription.handler
                if subscription.weak_ref and isinstance(handler, weakref.WeakMethod):
                    handler = handler()
                    if handler is None:
                        continue
                
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    # Wrap sync handler in async
                    async def wrapper(h=handler, e=event):
                        return h(e)
                    tasks.append(wrapper())
        
        if tasks:
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                self._logger.warning(f"Timeout waiting for handlers of {event_type}")
        
        return results
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get recent event history, optionally filtered by type"""
        if event_type:
            filtered = [e for e in self._event_history if e.type == event_type]
            return filtered[-limit:]
        return self._event_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event system statistics"""
        subscription_count = sum(len(subs) for subs in self._subscriptions.values())
        subscription_count += len(self._wildcard_subscriptions)
        
        return {
            **self._stats,
            "active_subscriptions": subscription_count,
            "event_types": len(self._subscriptions),
            "wildcard_subscriptions": len(self._wildcard_subscriptions),
            "history_size": len(self._event_history)
        }
    
    def clear_history(self):
        """Clear event history"""
        self._event_history.clear()
    
    def _get_matching_subscriptions(self, event_type: str) -> List[EventSubscription]:
        """Get all subscriptions that match the event type"""
        subscriptions = []
        
        # Direct matches
        if event_type in self._subscriptions:
            subscriptions.extend(self._subscriptions[event_type])
        
        # Wildcard matches
        for subscription in self._wildcard_subscriptions:
            if self._match_wildcard(subscription.event_type, event_type):
                subscriptions.append(subscription)
        
        return subscriptions
    
    def _match_wildcard(self, pattern: str, event_type: str) -> bool:
        """Check if event type matches wildcard pattern"""
        if '*' not in pattern:
            return pattern == event_type
        
        # Simple wildcard matching
        parts = pattern.split('*')
        if len(parts) == 2:
            prefix, suffix = parts
            return event_type.startswith(prefix) and event_type.endswith(suffix)
        
        return False
    
    def _sort_subscriptions(self, event_type: str):
        """Sort subscriptions by priority"""
        if event_type in self._subscriptions:
            self._subscriptions[event_type].sort(key=lambda s: s.priority.value, reverse=True)
        
        self._wildcard_subscriptions.sort(key=lambda s: s.priority.value, reverse=True)
    
    def _is_same_handler(self, handler1: Callable, handler2: Callable) -> bool:
        """Check if two handlers are the same"""
        if isinstance(handler1, weakref.WeakMethod):
            handler1 = handler1()
            if handler1 is None:
                return False
        
        return handler1 == handler2
    
    def _add_to_history(self, event: Event):
        """Add event to history with size limit"""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def _remove_subscription(self, subscription: EventSubscription):
        """Remove a subscription from appropriate collection"""
        # Remove from regular subscriptions
        for event_type, subs in self._subscriptions.items():
            if subscription in subs:
                subs.remove(subscription)
                return
        
        # Remove from wildcard subscriptions
        if subscription in self._wildcard_subscriptions:
            self._wildcard_subscriptions.remove(subscription)


# Global event manager instance
event_manager = EventManager()


# Decorator for easy event handling
def on_event(
    event_type: str,
    priority: EventPriority = EventPriority.NORMAL,
    once: bool = False,
    filter_func: Optional[Callable[[Event], bool]] = None
):
    """Decorator to register event handlers"""
    def decorator(func):
        event_manager.subscribe(
            event_type=event_type,
            handler=func,
            priority=priority,
            once=once,
            filter_func=filter_func
        )
        return func
    return decorator