"""
Health Tracker Plugin - Track health metrics and wellness
(DISABLED BY DEFAULT - Uncomment in config/plugins.yaml to enable)
"""
from core.plugin import Plugin
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from core.database import get_db


class HealthTrackerPlugin(Plugin):
    """Track health metrics, symptoms, medications, and workouts"""
    
    name = "Health Tracker"
    description = "Track health metrics, symptoms, medications, and wellness activities"
    version = "1.0.0"
    priority = 60
    
    keywords = [
        "health", "workout", "exercise", "symptom", "medicine",
        "medication", "weight", "sleep", "water", "steps",
        "calories", "pain", "headache", "sick", "feeling"
    ]
    
    async def initialize(self):
        """Initialize plugin"""
        self.metric_types = [
            'weight', 'sleep', 'water', 'steps', 'calories',
            'blood_pressure', 'heart_rate', 'mood'
        ]
        self.logger.info(f"{self.name} initialized")
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """Check if message is about health"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Handle health-related messages"""
        message_lower = message.lower()
        
        # Check for workout logging
        if any(word in message_lower for word in ["workout", "exercise", "gym", "ran", "run"]):
            return await self._log_workout(message)
        
        # Check for symptom logging
        if any(word in message_lower for word in ["symptom", "pain", "headache", "sick", "feeling"]):
            return await self._log_symptom(message)
        
        # Check for medication tracking
        if any(word in message_lower for word in ["medicine", "medication", "pill", "took"]):
            return await self._log_medication(message)
        
        # Check for metric logging
        if any(word in message_lower for word in self.metric_types):
            return await self._log_metric(message)
        
        # Check for health reports
        if any(word in message_lower for word in ["health report", "health summary", "how am i"]):
            return await self._health_report()
        
        return None
    
    async def _log_workout(self, message: str) -> str:
        """Log workout activity"""
        try:
            # Extract workout details
            details = await self.agent.ai_brain.extract_structured_data(
                message,
                {
                    "activity": "string - type of workout",
                    "duration_minutes": "number - how long",
                    "intensity": "string - low/medium/high",
                    "notes": "string - any additional details"
                }
            )
            
            # Store workout
            workout_data = await self.load_data('workouts') or []
            workout_data.append({
                'date': datetime.utcnow().isoformat(),
                'activity': details.get('activity', 'workout'),
                'duration': details.get('duration_minutes', 30),
                'intensity': details.get('intensity', 'medium'),
                'notes': details.get('notes', '')
            })
            await self.store_data('workouts', workout_data)
            
            return f"[OK] Logged workout: {details.get('activity', 'workout')} for {details.get('duration_minutes', 30)} minutes 💪"
            
        except Exception as e:
            self.logger.error(f"Failed to log workout: {e}")
            return "I had trouble logging that workout."
    
    async def _log_symptom(self, message: str) -> str:
        """Log health symptom"""
        try:
            # Extract symptom details
            details = await self.agent.ai_brain.extract_structured_data(
                message,
                {
                    "symptom": "string - what symptom",
                    "severity": "string - mild/moderate/severe",
                    "location": "string - where (if applicable)",
                    "notes": "string - additional context"
                }
            )
            
            # Store symptom
            symptoms = await self.load_data('symptoms') or []
            symptoms.append({
                'date': datetime.utcnow().isoformat(),
                'symptom': details.get('symptom', 'unknown'),
                'severity': details.get('severity', 'moderate'),
                'location': details.get('location', ''),
                'notes': details.get('notes', '')
            })
            await self.store_data('symptoms', symptoms)
            
            severity = details.get('severity', 'moderate')
            symptom = details.get('symptom', 'symptom')
            
            response = f"[OK] Logged {severity} {symptom}"
            
            # Pattern detection
            patterns = await self._detect_symptom_patterns(symptom)
            if patterns:
                response += f"\n\n💡 {patterns}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to log symptom: {e}")
            return "I had trouble logging that symptom."
    
    async def _log_medication(self, message: str) -> str:
        """Log medication taken"""
        try:
            details = await self.agent.ai_brain.extract_structured_data(
                message,
                {
                    "medication": "string - medication name",
                    "dosage": "string - how much",
                    "time": "string - when taken"
                }
            )
            
            meds = await self.load_data('medications') or []
            meds.append({
                'date': datetime.utcnow().isoformat(),
                'medication': details.get('medication', 'unknown'),
                'dosage': details.get('dosage', ''),
                'time': details.get('time', 'now')
            })
            await self.store_data('medications', meds)
            
            return f"[OK] Logged: {details.get('medication', 'medication')} {details.get('dosage', '')}"
            
        except Exception as e:
            self.logger.error(f"Failed to log medication: {e}")
            return "I had trouble logging that medication."
    
    async def _log_metric(self, message: str) -> str:
        """Log health metric"""
        try:
            # Determine metric type
            metric_type = None
            for m in self.metric_types:
                if m in message.lower():
                    metric_type = m
                    break
            
            if not metric_type:
                return None
            
            # Extract value
            details = await self.agent.ai_brain.extract_structured_data(
                message,
                {
                    "value": "number or string - the measurement",
                    "unit": "string - unit of measurement"
                }
            )
            
            metrics = await self.load_data(f'metrics_{metric_type}') or []
            metrics.append({
                'date': datetime.utcnow().isoformat(),
                'value': details.get('value'),
                'unit': details.get('unit', '')
            })
            await self.store_data(f'metrics_{metric_type}', metrics)
            
            emoji_map = {
                'weight': '⚖️',
                'sleep': '😴',
                'water': '💧',
                'steps': '👟',
                'mood': '😊'
            }
            emoji = emoji_map.get(metric_type, '📊')
            
            return f"[OK] Logged {metric_type}: {details.get('value')} {details.get('unit', '')} {emoji}"
            
        except Exception as e:
            self.logger.error(f"Failed to log metric: {e}")
            return "I had trouble logging that metric."
    
    async def _detect_symptom_patterns(self, symptom: str) -> Optional[str]:
        """Detect patterns in symptoms"""
        try:
            symptoms = await self.load_data('symptoms') or []
            
            # Check for recent occurrences
            recent_symptoms = [
                s for s in symptoms
                if s.get('symptom') == symptom and
                   datetime.fromisoformat(s['date']) > datetime.utcnow() - timedelta(days=7)
            ]
            
            if len(recent_symptoms) >= 3:
                return f"You've logged '{symptom}' {len(recent_symptoms)} times this week. Consider tracking triggers."
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to detect patterns: {e}")
            return None
    
    async def _health_report(self) -> str:
        """Generate health summary"""
        try:
            workouts = await self.load_data('workouts') or []
            symptoms = await self.load_data('symptoms') or []
            
            # Last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            recent_workouts = [
                w for w in workouts
                if datetime.fromisoformat(w['date']) > week_ago
            ]
            
            recent_symptoms = [
                s for s in symptoms
                if datetime.fromisoformat(s['date']) > week_ago
            ]
            
            response = "🏥 **Health Summary (Last 7 Days):**\n\n"
            
            if recent_workouts:
                total_minutes = sum(w.get('duration', 0) for w in recent_workouts)
                response += f"💪 Workouts: {len(recent_workouts)} sessions ({total_minutes} min total)\n"
            else:
                response += "💪 Workouts: None logged\n"
            
            if recent_symptoms:
                response += f"⚠️ Symptoms logged: {len(recent_symptoms)}\n"
            else:
                response += "[OK] No symptoms logged\n"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return "I had trouble generating your health report."
    
    def get_commands(self) -> Dict[str, str]:
        """Get available commands"""
        return {
            "I worked out for [X] minutes": "Log workout",
            "Log symptom: [description]": "Track health symptoms",
            "I took [medication]": "Log medication",
            "My weight is [X] lbs": "Track health metrics",
            "Health report": "View health summary"
        }
