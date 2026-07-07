"""SID Soul - The personality and memory core of the operating system.
This is the 'soul file' that defines who SID is, how it behaves,
and what it remembers about each user."""
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

@dataclass
class SoulPersonality:
    """The personality definition of SID."""
    name: str = "SID"
    title: str = "Super Intelligent Distro"
    version: str = "0.5.1"
    
    # Core traits
    traits: List[str] = field(default_factory=lambda: [
        "helpful", "direct", "retro-enthusiast", "resourceful",
        "efficient", "patient", "knowledgeable", "humble"
    ])
    
    # Communication style
    style: str = "professional_retro"  # professional, casual, retro, minimal
    catchphrase: str = "Type anything. I understand."
    
    # Relationship with user
    formality: float = 0.4  # 0=casual, 1=formal
    creativity: float = 0.6  # 0=literal, 1=creative
    verbosity: float = 0.3  # 0=minimal, 1=verbose
    
    # Memory preferences
    remember_user_preferences: bool = True
    remember_errors: bool = True
    remember_accomplishments: bool = True
    context_compression_style: str = "smart"  # smart, aggressive, minimal
    
    # System attitude
    system_caution: float = 0.3  # 0=let user do anything, 1=double-check everything
    proactiveness: float = 0.5  # 0=wait for commands, 1=suggest actions
    
    # AI model preferences
    preferred_model: str = "auto"
    fallback_to_api: bool = True
    router_enabled: bool = True
    specialist_swapping: bool = True


@dataclass
class UserProfile:
    """What SID knows about a user."""
    username: str = "user"
    skill_level: str = "beginner"  # beginner, intermediate, advanced, expert
    interests: List[str] = field(default_factory=list)
    frequent_tasks: List[str] = field(default_factory=list)
    known_commands: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_count: int = 0
    first_seen: float = 0.0
    last_seen: float = 0.0
    achievements: List[str] = field(default_factory=list)
    
    # Learning progress
    skills_learned: List[str] = field(default_factory=list)
    tools_used: Dict[str, int] = field(default_factory=dict)
    topics_explored: List[str] = field(default_factory=list)


class Soul:
    """The 'soul file' - persistent personality and memory core.
    
    This is the central file that defines SID's identity, remembers
    users, and maintains the OS's personality across sessions."""

    def __init__(self, soul_path: str = "/etc/sid/soul.json"):
        self.soul_path = Path(soul_path)
        self.personality: SoulPersonality = SoulPersonality()
        self.users: Dict[str, UserProfile] = {}
        self.current_user: str = "user"
        self._load()
    
    def _load(self):
        """Load soul from file or create default."""
        if self.soul_path.exists():
            try:
                data = json.loads(self.soul_path.read_text())
                if "personality" in data:
                    self.personality = SoulPersonality(**data["personality"])
                if "users" in data:
                    for name, profile in data["users"].items():
                        self.users[name] = UserProfile(**profile)
                if "current_user" in data:
                    self.current_user = data["current_user"]
            except Exception as e:
                print(f"[SID Soul] Load error: {e}")
        
        self.save()
    
    def save(self):
        """Save soul to file."""
        self.soul_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "personality": asdict(self.personality),
            "users": {name: asdict(profile) for name, profile in self.users.items()},
            "current_user": self.current_user,
            "saved_at": time.time(),
            "version": "0.5.1"
        }
        self.soul_path.write_text(json.dumps(data, indent=2))
    
    def get_user(self, username: str = "") -> UserProfile:
        """Get or create user profile."""
        name = username or self.current_user
        if name not in self.users:
            self.users[name] = UserProfile(
                username=name,
                first_seen=time.time(),
                last_seen=time.time()
            )
            self.save()
        return self.users[name]
    
    def update_user(self, username: str = "", **updates):
        """Update user profile attributes."""
        user = self.get_user(username)
        for key, val in updates.items():
            if hasattr(user, key):
                setattr(user, key, val)
        user.last_seen = time.time()
        user.interaction_count += 1
        self.save()
    
    def record_interaction(self, user_input: str, response: str, intent: str = "general"):
        """Record an interaction and learn from it."""
        user = self.get_user()
        
        # Track topics
        topics = [intent]
        user.topics_explored.extend(topics)
        user.topics_explored = list(set(user.topics_explored))[-50:]
        
        # Track tools used
        if intent in user.tools_used:
            user.tools_used[intent] += 1
        else:
            user.tools_used[intent] = 1
        
        user.last_seen = time.time()
        self.save()
    
    def get_personality_dict(self) -> Dict:
        """Get personality as dict for prompt injection."""
        p = self.personality
        return {
            "name": p.name,
            "traits": ", ".join(p.traits[:5]),
            "style": p.style,
            "catchphrase": p.catchphrase,
            "formality": p.formality,
            "creativity": p.creativity,
        }
    
    def get_user_context(self) -> Dict:
        """Get user context for AI prompts."""
        user = self.get_user()
        return {
            "username": user.username,
            "skill_level": user.skill_level,
            "interests": user.interests[-5:],
            "frequent_tasks": user.frequent_tasks[-5:],
            "interaction_count": user.interaction_count,
            "achievements": user.achievements[-5:],
        }
    
    def set_personality(self, **settings):
        """Update personality settings."""
        for key, val in settings.items():
            if hasattr(self.personality, key):
                setattr(self.personality, key, val)
        self.save()
    
    def get_personality_text(self) -> str:
        """Get a formatted personality description."""
        p = self.personality
        return (
            f"I am {p.name}, the {p.title}.\n"
            f"My personality: {', '.join(p.traits)}.\n"
            f"I communicate in a {p.style.replace('_', ' ')} style.\n"
            f"My motto: '{p.catchphrase}'"
        )

    def get_achievement(self, name: str, description: str) -> bool:
        """Award an achievement to the user."""
        user = self.get_user()
        achievement = f"{name}: {description}"
        if achievement not in user.achievements:
            user.achievements.append(achievement)
            self.save()
            return True
        return False
