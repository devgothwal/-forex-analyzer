"""
ML Pipeline - Machine Learning analysis for trading patterns
Implements clustering, classification, and predictive modeling
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging
import pickle
from pathlib import Path

# ML libraries
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, silhouette_score
import joblib

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from app.models.trading_data import TradingData, Trade
from app.core.config import settings
from app.core.event_system import event_manager

logger = logging.getLogger(__name__)


class MLPipeline:
    """Machine Learning pipeline for trading analysis"""
    
    def __init__(self):
        self.feature_columns = [
            'hour', 'day_of_week_encoded', 'size', 'duration_minutes',
            'pips', 'session_encoded', 'symbol_encoded'
        ]
        self.scalers = {}
        self.encoders = {}
        self.models = {}
    
    async def run_quick_analysis(self, data: TradingData) -> Dict[str, Any]:
        """Run quick ML analysis for comprehensive reports"""
        
        if len(data.trades) < 10:
            return {"error": "Insufficient data for ML analysis (minimum 10 trades required)"}
        
        # Prepare features
        features_df = await self._prepare_features(data.trades)
        
        results = {}
        
        # Quick clustering
        if len(features_df) >= 5:
            clustering_result = await self._quick_clustering(features_df)
            results['clustering'] = clustering_result
        
        # Feature importance
        if len(features_df) >= 20:
            importance_result = await self._analyze_feature_importance(features_df)
            results['feature_importance'] = importance_result
        
        # Anomaly detection
        anomalies = await self._detect_anomalies(features_df)
        results['anomalies'] = anomalies
        
        return results
    
    async def run_clustering_analysis(self, data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run detailed clustering analysis"""
        
        if len(data.trades) < 5:
            return {"error": "Insufficient data for clustering (minimum 5 trades required)"}
        
        features_df = await self._prepare_features(data.trades)
        
        algorithm = params.get('algorithm', 'kmeans')
        n_clusters = params.get('n_clusters', 5)
        
        if algorithm == 'kmeans':
            results = await self._run_kmeans_clustering(features_df, n_clusters)
        elif algorithm == 'dbscan':
            results = await self._run_dbscan_clustering(features_df, params)
        else:
            return {"error": f"Unknown clustering algorithm: {algorithm}"}
        
        # Add trade assignments back to results
        results['trade_clusters'] = await self._assign_trades_to_clusters(data.trades, results)
        
        await event_manager.emit("ml_clustering_completed", {
            "algorithm": algorithm,
            "clusters_found": results.get('n_clusters', 0),
            "silhouette_score": results.get('silhouette_score', 0)
        })
        
        return results
    
    async def run_classification_analysis(self, data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run classification analysis to predict trade outcomes"""
        
        if len(data.trades) < 20:
            return {"error": "Insufficient data for classification (minimum 20 trades required)"}
        
        features_df = await self._prepare_features(data.trades)
        
        # Create target variable (profitable vs unprofitable)
        target = (features_df['profit'] > 0).astype(int)
        
        # Remove target from features
        X = features_df.drop(['profit'], axis=1, errors='ignore')
        y = target
        
        model_type = params.get('model', 'random_forest')
        use_cv = params.get('cross_validation', True)
        
        results = await self._train_classification_model(X, y, model_type, use_cv)
        
        # Feature importance
        if hasattr(results['model'], 'feature_importances_'):
            feature_importance = dict(zip(X.columns, results['model'].feature_importances_))
            results['feature_importance'] = {k: round(v, 4) for k, v in feature_importance.items()}
        
        # SHAP analysis if available
        if SHAP_AVAILABLE and len(X) <= 1000:  # Limit for performance
            try:
                shap_values = await self._calculate_shap_values(results['model'], X)
                results['shap_analysis'] = shap_values
            except Exception as e:
                logger.warning(f"SHAP analysis failed: {e}")
        
        await event_manager.emit("ml_classification_completed", {
            "model_type": model_type,
            "accuracy": results.get('accuracy', 0),
            "train_size": len(X)
        })
        
        return results
    
    async def _prepare_features(self, trades: List[Trade]) -> pd.DataFrame:
        """Prepare features for ML analysis"""
        
        data = []
        for trade in trades:
            if not trade.open_time:
                continue
                
            open_time = pd.to_datetime(trade.open_time)
            
            # Calculate duration in minutes
            if trade.close_time:
                close_time = pd.to_datetime(trade.close_time)
                duration_minutes = (close_time - open_time).total_seconds() / 60
            else:
                duration_minutes = 0
            
            # Determine trading session
            hour = open_time.hour
            session = self._get_trading_session(hour)
            
            feature_row = {
                'profit': trade.profit,
                'hour': hour,
                'day_of_week': open_time.day_name(),
                'size': trade.size,
                'duration_minutes': duration_minutes,
                'pips': trade.pips or 0,
                'session': session,
                'symbol': trade.symbol,
                'type': trade.type,
                'commission': trade.commission,
                'swap': trade.swap
            }
            data.append(feature_row)
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return df
        
        # Encode categorical variables
        le_day = LabelEncoder()
        le_session = LabelEncoder()
        le_symbol = LabelEncoder()
        le_type = LabelEncoder()
        
        if 'day_of_week' in df.columns:
            df['day_of_week_encoded'] = le_day.fit_transform(df['day_of_week'])
        if 'session' in df.columns:
            df['session_encoded'] = le_session.fit_transform(df['session'])
        if 'symbol' in df.columns:
            df['symbol_encoded'] = le_symbol.fit_transform(df['symbol'])
        if 'type' in df.columns:
            df['type_encoded'] = le_type.fit_transform(df['type'])
        
        # Store encoders for later use
        self.encoders = {
            'day_of_week': le_day,
            'session': le_session,
            'symbol': le_symbol,
            'type': le_type
        }
        
        # Fill missing values
        df = df.fillna(0)
        
        return df
    
    def _get_trading_session(self, hour: int) -> str:
        """Determine trading session based on hour"""
        
        sessions = {
            'Sydney': {'start': 21, 'end': 6},
            'Tokyo': {'start': 23, 'end': 8},
            'London': {'start': 7, 'end': 16},
            'New York': {'start': 12, 'end': 21}
        }
        
        for session, times in sessions.items():
            start, end = times['start'], times['end']
            
            if start > end:  # Session spans midnight
                if hour >= start or hour < end:
                    return session
            else:  # Normal session
                if start <= hour < end:
                    return session
        
        return 'Other'
    
    async def _quick_clustering(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run quick clustering analysis"""
        
        # Select features for clustering
        feature_cols = [col for col in self.feature_columns if col in df.columns]
        if not feature_cols:
            return {"error": "No valid features for clustering"}
        
        X = df[feature_cols].copy()
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine optimal number of clusters (simple heuristic)
        n_samples = len(X)
        n_clusters = min(max(2, n_samples // 5), 8)  # Between 2 and 8 clusters
        
        # Run KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Calculate silhouette score
        silhouette_avg = silhouette_score(X_scaled, clusters)
        
        # Analyze clusters
        df_with_clusters = df.copy()
        df_with_clusters['cluster'] = clusters
        
        cluster_analysis = {}
        for cluster_id in range(n_clusters):
            cluster_data = df_with_clusters[df_with_clusters['cluster'] == cluster_id]
            cluster_analysis[f'cluster_{cluster_id}'] = {
                'size': len(cluster_data),
                'avg_profit': float(cluster_data['profit'].mean()),
                'total_profit': float(cluster_data['profit'].sum()),
                'win_rate': float((cluster_data['profit'] > 0).mean()),
                'characteristics': await self._describe_cluster(cluster_data, feature_cols)
            }
        
        return {
            'n_clusters': n_clusters,
            'silhouette_score': round(silhouette_avg, 3),
            'cluster_analysis': cluster_analysis,
            'algorithm': 'kmeans'
        }
    
    async def _run_kmeans_clustering(self, df: pd.DataFrame, n_clusters: int) -> Dict[str, Any]:
        """Run detailed KMeans clustering"""
        
        feature_cols = [col for col in self.feature_columns if col in df.columns]
        X = df[feature_cols].copy()
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['clustering'] = scaler
        
        # Run KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Calculate metrics
        silhouette_avg = silhouette_score(X_scaled, clusters)
        inertia = kmeans.inertia_
        
        # Save model
        model_path = settings.get_model_path() / "kmeans_model.joblib"
        joblib.dump(kmeans, model_path)
        
        # Analyze clusters
        return await self._analyze_clusters(df, clusters, n_clusters, {
            'silhouette_score': silhouette_avg,
            'inertia': inertia,
            'algorithm': 'kmeans'
        })
    
    async def _run_dbscan_clustering(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run DBSCAN clustering"""
        
        feature_cols = [col for col in self.feature_columns if col in df.columns]
        X = df[feature_cols].copy()
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # DBSCAN parameters
        eps = params.get('eps', 0.5)
        min_samples = params.get('min_samples', 5)
        
        # Run DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(X_scaled)
        
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_noise = list(clusters).count(-1)
        
        if n_clusters < 2:
            return {"error": "DBSCAN found less than 2 clusters. Try adjusting parameters."}
        
        # Calculate silhouette score (excluding noise points)
        if n_clusters > 1:
            mask = clusters != -1
            if mask.sum() > 1:
                silhouette_avg = silhouette_score(X_scaled[mask], clusters[mask])
            else:
                silhouette_avg = 0
        else:
            silhouette_avg = 0
        
        return await self._analyze_clusters(df, clusters, n_clusters, {
            'silhouette_score': silhouette_avg,
            'n_noise': n_noise,
            'eps': eps,
            'min_samples': min_samples,
            'algorithm': 'dbscan'
        })
    
    async def _analyze_clusters(self, df: pd.DataFrame, clusters: np.ndarray, n_clusters: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze clustering results"""
        
        df_with_clusters = df.copy()
        df_with_clusters['cluster'] = clusters
        
        cluster_analysis = {}
        
        for cluster_id in range(n_clusters):
            cluster_data = df_with_clusters[df_with_clusters['cluster'] == cluster_id]
            
            if len(cluster_data) == 0:
                continue
            
            # Calculate cluster statistics
            avg_profit = cluster_data['profit'].mean()
            total_profit = cluster_data['profit'].sum()
            win_rate = (cluster_data['profit'] > 0).mean()
            
            # Dominant characteristics
            characteristics = {}
            if 'session' in cluster_data.columns:
                characteristics['dominant_session'] = cluster_data['session'].mode().iloc[0] if not cluster_data['session'].mode().empty else 'Unknown'
            if 'symbol' in cluster_data.columns:
                characteristics['dominant_symbol'] = cluster_data['symbol'].mode().iloc[0] if not cluster_data['symbol'].mode().empty else 'Unknown'
            if 'type' in cluster_data.columns:
                characteristics['dominant_type'] = cluster_data['type'].mode().iloc[0] if not cluster_data['type'].mode().empty else 'Unknown'
            
            characteristics['avg_size'] = float(cluster_data['size'].mean())
            characteristics['avg_duration'] = float(cluster_data['duration_minutes'].mean())
            
            cluster_analysis[f'cluster_{cluster_id}'] = {
                'size': len(cluster_data),
                'avg_profit': round(avg_profit, 2),
                'total_profit': round(total_profit, 2),
                'win_rate': round(win_rate * 100, 2),
                'characteristics': characteristics
            }
        
        # Handle noise points for DBSCAN
        if -1 in clusters:
            noise_data = df_with_clusters[df_with_clusters['cluster'] == -1]
            cluster_analysis['noise'] = {
                'size': len(noise_data),
                'avg_profit': round(noise_data['profit'].mean(), 2),
                'total_profit': round(noise_data['profit'].sum(), 2),
                'win_rate': round((noise_data['profit'] > 0).mean() * 100, 2)
            }
        
        result = {
            'n_clusters': n_clusters,
            'cluster_analysis': cluster_analysis,
            **metrics
        }
        
        return result
    
    async def _train_classification_model(self, X: pd.DataFrame, y: pd.Series, model_type: str, use_cv: bool) -> Dict[str, Any]:
        """Train classification model"""
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['classification'] = scaler
        
        # Select model
        if model_type == 'random_forest':
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == 'decision_tree':
            model = DecisionTreeClassifier(random_state=42, max_depth=10)
        elif model_type == 'xgboost' and XGBOOST_AVAILABLE:
            model = xgb.XGBClassifier(random_state=42)
        else:
            model = RandomForestClassifier(n_estimators=100, random_state=42)  # Default fallback
        
        # Train model
        model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = model.predict(X_test_scaled)
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        # Cross-validation
        cv_scores = []
        if use_cv and len(X_train) > 10:
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=min(5, len(X_train) // 2))
        
        # Save model
        model_path = settings.get_model_path() / f"{model_type}_model.joblib"
        joblib.dump(model, model_path)
        self.models[model_type] = model
        
        # Classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        return {
            'model': model,
            'model_type': model_type,
            'train_accuracy': round(train_score, 3),
            'test_accuracy': round(test_score, 3),
            'cv_scores': [round(score, 3) for score in cv_scores] if cv_scores.size > 0 else [],
            'cv_mean': round(cv_scores.mean(), 3) if cv_scores.size > 0 else 0,
            'cv_std': round(cv_scores.std(), 3) if cv_scores.size > 0 else 0,
            'classification_report': report,
            'accuracy': round(test_score, 3)
        }
    
    async def _analyze_feature_importance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze feature importance using Random Forest"""
        
        target = (df['profit'] > 0).astype(int)
        feature_cols = [col for col in self.feature_columns if col in df.columns]
        
        if not feature_cols:
            return {"error": "No valid features for importance analysis"}
        
        X = df[feature_cols]
        y = target
        
        # Train Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        # Feature importance
        importances = rf.feature_importances_
        feature_importance = dict(zip(feature_cols, importances))
        
        # Sort by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'feature_importance': {k: round(v, 4) for k, v in sorted_features},
            'most_important': sorted_features[0][0] if sorted_features else None,
            'least_important': sorted_features[-1][0] if sorted_features else None
        }
    
    async def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalous trades using statistical methods"""
        
        anomalies = []
        
        # Profit anomalies (outliers)
        profit_q1 = df['profit'].quantile(0.25)
        profit_q3 = df['profit'].quantile(0.75)
        profit_iqr = profit_q3 - profit_q1
        profit_lower = profit_q1 - 1.5 * profit_iqr
        profit_upper = profit_q3 + 1.5 * profit_iqr
        
        profit_outliers = df[(df['profit'] < profit_lower) | (df['profit'] > profit_upper)]
        
        # Size anomalies
        if 'size' in df.columns:
            size_q1 = df['size'].quantile(0.25)
            size_q3 = df['size'].quantile(0.75)
            size_iqr = size_q3 - size_q1
            size_lower = size_q1 - 1.5 * size_iqr
            size_upper = size_q3 + 1.5 * size_iqr
            
            size_outliers = df[(df['size'] < size_lower) | (df['size'] > size_upper)]
        else:
            size_outliers = pd.DataFrame()
        
        # Duration anomalies
        if 'duration_minutes' in df.columns and df['duration_minutes'].max() > 0:
            duration_q1 = df['duration_minutes'].quantile(0.25)
            duration_q3 = df['duration_minutes'].quantile(0.75)
            duration_iqr = duration_q3 - duration_q1
            duration_upper = duration_q3 + 1.5 * duration_iqr
            
            duration_outliers = df[df['duration_minutes'] > duration_upper]
        else:
            duration_outliers = pd.DataFrame()
        
        return {
            'profit_outliers': len(profit_outliers),
            'size_outliers': len(size_outliers),
            'duration_outliers': len(duration_outliers),
            'total_anomalies': len(set(profit_outliers.index) | set(size_outliers.index) | set(duration_outliers.index)),
            'anomaly_rate': round((len(set(profit_outliers.index) | set(size_outliers.index) | set(duration_outliers.index)) / len(df) * 100), 2)
        }
    
    async def _calculate_shap_values(self, model, X: pd.DataFrame) -> Dict[str, Any]:
        """Calculate SHAP values for model interpretability"""
        
        if not SHAP_AVAILABLE:
            return {"error": "SHAP not available"}
        
        try:
            # Create explainer
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            
            # For binary classification, take the positive class
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            # Calculate mean absolute SHAP values
            mean_shap = np.abs(shap_values).mean(0)
            feature_importance = dict(zip(X.columns, mean_shap))
            
            return {
                'feature_importance': {k: round(v, 4) for k, v in feature_importance.items()},
                'shap_available': True
            }
        
        except Exception as e:
            logger.error(f"SHAP calculation failed: {e}")
            return {"error": f"SHAP calculation failed: {str(e)}"}
    
    async def _assign_trades_to_clusters(self, trades: List[Trade], cluster_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assign individual trades to their clusters"""
        
        # This would require storing cluster assignments during clustering
        # For now, return summary
        return {
            "note": "Individual trade cluster assignments require full clustering pipeline",
            "cluster_count": cluster_results.get('n_clusters', 0)
        }
    
    async def _describe_cluster(self, cluster_data: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
        """Describe cluster characteristics"""
        
        characteristics = {}
        
        for col in feature_cols:
            if col in cluster_data.columns:
                if cluster_data[col].dtype in ['object', 'category']:
                    # Categorical: most common value
                    mode_val = cluster_data[col].mode()
                    characteristics[col] = mode_val.iloc[0] if not mode_val.empty else 'Unknown'
                else:
                    # Numerical: mean
                    characteristics[col] = round(cluster_data[col].mean(), 2)
        
        return characteristics