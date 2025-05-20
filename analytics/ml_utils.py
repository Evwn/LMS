import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from collections import defaultdict
import pandas as pd

class LearnerInsightsGenerator:
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.kmeans = KMeans(n_clusters=3, random_state=42)

    def prepare_student_data(self, student_performances):
        """Convert student performance data to features for ML analysis"""
        features = []
        for perf in student_performances:
            features.append([
                float(perf.quiz_average),
                float(perf.assignment_average),
                float(perf.attendance_rate),
                float(perf.participation_score),
                float(perf.overall_grade)
            ])
        return np.array(features)

    def generate_learning_patterns(self, student_performances):
        """Identify learning patterns using clustering"""
        if not student_performances:
            return []

        features = self.prepare_student_data(student_performances)
        scaled_features = self.scaler.fit_transform(features)
        
        # Apply PCA for dimensionality reduction
        reduced_features = self.pca.fit_transform(scaled_features)
        
        # Apply clustering
        clusters = self.kmeans.fit_predict(reduced_features)
        
        # Analyze patterns
        patterns = []
        for i, cluster in enumerate(np.unique(clusters)):
            cluster_data = features[clusters == cluster]
            pattern = {
                'pattern_type': f'Learning Pattern {i+1}',
                'avg_quiz': np.mean(cluster_data[:, 0]),
                'avg_assignment': np.mean(cluster_data[:, 1]),
                'avg_attendance': np.mean(cluster_data[:, 2]),
                'avg_participation': np.mean(cluster_data[:, 3]),
                'avg_grade': np.mean(cluster_data[:, 4]),
                'count': len(cluster_data)
            }
            patterns.append(pattern)
        
        return patterns

    def generate_personalized_recommendations(self, student_performance):
        """Generate personalized recommendations based on performance metrics"""
        recommendations = []
        
        # Quiz performance analysis
        if student_performance.quiz_average < 70:
            recommendations.append({
                'area': 'Quiz Performance',
                'recommendation': 'Consider spending more time reviewing course materials before quizzes',
                'priority': 'high'
            })
        
        # Assignment completion analysis
        if student_performance.assignment_average < 70:
            recommendations.append({
                'area': 'Assignment Completion',
                'recommendation': 'Start assignments earlier and seek help when needed',
                'priority': 'high'
            })
        
        # Attendance analysis
        if student_performance.attendance_rate < 80:
            recommendations.append({
                'area': 'Attendance',
                'recommendation': 'Improve class attendance to better understand course materials',
                'priority': 'medium'
            })
        
        # Participation analysis
        if student_performance.participation_score < 60:
            recommendations.append({
                'area': 'Class Participation',
                'recommendation': 'Increase engagement in class discussions and activities',
                'priority': 'medium'
            })
        
        return recommendations

    def predict_performance_trend(self, historical_performances):
        """Predict future performance trend based on historical data"""
        if len(historical_performances) < 3:
            return "Insufficient data for trend prediction"
        
        grades = [float(p.overall_grade) for p in historical_performances]
        trend = np.polyfit(range(len(grades)), grades, 1)[0]
        
        if trend > 2:
            return "Strong upward trend in performance"
        elif trend > 0:
            return "Slight improvement in performance"
        elif trend > -2:
            return "Slight decline in performance"
        else:
            return "Significant decline in performance"

    def identify_learning_style(self, student_performance):
        """Identify student's learning style based on performance metrics"""
        quiz_weight = float(student_performance.quiz_average)
        assignment_weight = float(student_performance.assignment_average)
        participation_weight = float(student_performance.participation_score)
        
        if quiz_weight > assignment_weight and quiz_weight > participation_weight:
            return "Test-oriented learner"
        elif assignment_weight > quiz_weight and assignment_weight > participation_weight:
            return "Project-based learner"
        elif participation_weight > quiz_weight and participation_weight > assignment_weight:
            return "Interactive learner"
        else:
            return "Balanced learner"

    def generate_insights_report(self, student_performance, historical_performances):
        """Generate comprehensive insights report"""
        insights = {
            'learning_style': self.identify_learning_style(student_performance),
            'performance_trend': self.predict_performance_trend(historical_performances),
            'recommendations': self.generate_personalized_recommendations(student_performance),
            'strengths': [],
            'areas_for_improvement': []
        }
        
        # Identify strengths
        if student_performance.quiz_average >= 80:
            insights['strengths'].append("Strong quiz performance")
        if student_performance.assignment_average >= 80:
            insights['strengths'].append("Consistent assignment completion")
        if student_performance.attendance_rate >= 90:
            insights['strengths'].append("Excellent attendance record")
        if student_performance.participation_score >= 80:
            insights['strengths'].append("Active class participation")
        
        # Identify areas for improvement
        if student_performance.quiz_average < 70:
            insights['areas_for_improvement'].append("Quiz performance needs improvement")
        if student_performance.assignment_average < 70:
            insights['areas_for_improvement'].append("Assignment completion rate could be better")
        if student_performance.attendance_rate < 80:
            insights['areas_for_improvement'].append("Attendance needs improvement")
        if student_performance.participation_score < 60:
            insights['areas_for_improvement'].append("Class participation could be increased")
        
        return insights 