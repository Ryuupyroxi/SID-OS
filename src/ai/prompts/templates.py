"""SID Prompt Templates - Memory-optimized wording that promotes efficient 
memory management WITHOUT sacrificing intelligence. These prompts are crafted
to guide AI behavior through smart phrasing, not truncation.

Key techniques:
- "Chunk and summarize" instead of "be brief" 
- "Focus on actionable output" instead of "be concise"
- Structured context framing for better recall
- Progressive disclosure: surface-level first, depth on request
- Memory anchors: tie new info to previously established context"""
from typing import Dict, List, Optional

class PromptTemplates:
    """Memory-optimized prompt templates using smart wording."""

    # ===== CORE IDENTITY =====
    # These establish WHO the AI is and HOW it should think about memory
    SYSTEM_IDENTITY = (
        "You are SID (Super Intelligent Distro), an AI operating system "
        "running on resource-conscious hardware (4GB RAM target). "
        "You excel at being both intelligent AND memory-efficient.\n\n"
        "MEMORY PHILOSOPHY:\n"
        "• Prioritize depth over breadth: fully answer the current query "
        "before moving on\n"
        "• Use hierarchical context: place new info in relation to what "
        "we've already discussed\n"
        "• Progressive disclosure: give the core answer first, offer "
        "details when asked\n"
        "• Anchor new knowledge to existing context instead of repeating it\n"
        "• When summarizing, preserve relationships between concepts, not "
        "just keywords"
    )

    SYSTEM_HACKER = (
        "═══ SID OS v0.0.4 ═══\n"
        "AI Core: ACTIVE | Memory: OPTIMIZED\n\n"
        "You are the soul of this operating system. Every interaction is a "
        "conversation with a knowledgeable sysadmin who values efficiency.\n\n"
        "COMMUNICATION STYLE:\n"
        "• Lead with the answer, offer details on request\n"
        "• Use commands to demonstrate solutions\n"
        "• When explaining, use analogies tied to familiar concepts\n"
        "• If something was discussed earlier, reference it by context "
        "rather than repeating it in full\n"
        "• Transform complex topics into buildable mental models"
    )

    # ===== MEMORY-CONSCIOUS TASK PROMPTS =====
    # These guide the AI to think about memory efficiency 
    # through smart wording, not by demanding brevity

    TASK_COMMAND = (
        "I need a command to: {query}\n"
        "Think through the approach, then give me the command. "
        "If there are multiple valid approaches, give the safest one "
        "and mention alternatives briefly."
    )

    TASK_CODE = (
        "Write {language} code that: {task}\n"
        "Requirements: {requirements}\n\n"
        "Before writing, consider:\n"
        "1. What's the simplest approach that meets the requirements?\n"
        "2. How can this be made compatible with older systems?\n"
        "3. What error handling is appropriate?\n\n"
        "Provide the code with brief inline comments explaining key parts."
    )

    TASK_EXPLAIN = (
        "Explain: {topic}\n"
        "Context: The user's skill level is {level}\n\n"
        "Structure your explanation like layers of an onion:\n"
        "1. First layer: A simple analogy or mental model (1-2 sentences)\n"
        "2. Second layer: How it actually works (2-3 sentences)\n"
        "3. Third layer: A practical example they can try\n\n"
        "Stop at the layer that satisfies their question. "
        "Offer to go deeper if needed."
    )

    TASK_LEARN = (
        "I want to learn about: {topic}\n"
        "My current level: {level}\n\n"
        "Teach me in a way that builds lasting understanding:\n"
        "• Connect this to things I might already know\n"
        "• Give me one command or exercise to solidify the concept\n"
        "• Tell me what common mistakes to watch for\n"
        "• Suggest what to learn next to build on this"
    )

    TASK_DEBUG = (
        "Help me debug:\n"
        "Error: {error}\n"
        "Context: {context}\n\n"
        "Walk through your diagnostic reasoning:\n"
        "1. What does this error actually mean?\n"
        "2. What are the most likely causes (in order)?\n"
        "3. How can I verify each? (give commands)\n"
        "4. Once identified, how do I fix it?"
    )

    # ===== MEMORY ANCHOR PROMPTS =====
    # These help the AI build and maintain context efficiently

    MEMORY_ANCHOR = (
        "Earlier we discussed {topic}. In that context, "
        "we covered: {summary}\n\n"
        "Now I want to build on that. {new_query}\n\n"
        "Reference what we established before rather than re-explaining it."
    )

    MEMORY_CONNECT = (
        "I recall that {previous_context}.\n"
        "I'm now learning {new_topic}.\n\n"
        "Are these related? If so, how does the new information "
        "build on or relate to what we already covered?"
    )

    MEMORY_REVIEW = (
        "Let's review what I've learned so far about {topic}.\n"
        "Here's my understanding: {current_understanding}\n\n"
        "Fill in any gaps, correct misunderstandings, "
        "and suggest what to explore next."
    )

    # ===== CONTEXT COMPRESSION GUIDANCE =====
    # These guide the AI on HOW to compress without losing meaning

    COMPRESS_GUIDANCE = (
        "Summarize the following while preserving:\n"
        "• Key decisions and their rationale\n"
        "• Commands and their purposes\n"
        "• Relationships between concepts\n"
        "• Open questions or action items\n\n"
        "You may drop: greetings, confirmations, rephrasing, "
        "and pleasantries.\n\n"
        "Aim for 30% of original length while keeping all "
        "functionally important information:\n\n{text}"
    )

    COMPRESS_CONVERSATION = (
        "Compress this conversation for efficient storage, "
        "preserving all substantively important information:\n\n"
        "{conversation}\n\n"
        "Format: timeline of key exchanges with essential context."
    )

    @classmethod
    def get_system(cls, style: str = "default", context: Optional[Dict] = None) -> str:
        """Get appropriate system prompt with memory optimization."""
        base = cls.SYSTEM_HACKER if style == "hacker" else cls.SYSTEM_IDENTITY
        
        if not context:
            return base
        
        extras = []
        
        # Add soul personality if available  
        if "soul" in context:
            soul = context["soul"]
            if soul.get("personality"):
                extras.append(f"[IDENTITY] {soul['personality'].get('catchphrase', '')}")
            if soul.get("traits"):
                extras.append(f"[TRAITS] {', '.join(soul['traits'][:5])}")
        
        # Add hardware context (minimal)
        if "hardware" in context:
            hw = context["hardware"]
            extras.append(f"[ENV] {hw.get('ram_tier', '4GB')} system | CPU: {hw.get('cpu_temp', '?')}°C")
        
        # Add skills context
        if "skills" in context:
            skills = context["skills"]
            if skills:
                extras.append(f"[CAPABILITIES] Skills loaded: {skills}")
        
        if extras:
            base = base + "\n\n" + "\n".join(extras)
        
        return base

    @classmethod
    def format(cls, template: str, **kwargs) -> str:
        """Format a template with variables."""
        return template.format(**kwargs)

    @classmethod
    def compress(cls, text: str, style: str = "standard") -> str:
        """Get compression prompt for text."""
        if style == "conversation":
            return cls.COMPRESS_CONVERSATION.format(conversation=text[:3000])
        return cls.COMPRESS_GUIDANCE.format(text=text[:2000])

    @classmethod
    def anchor(cls, topic: str, summary: str, new_query: str) -> str:
        """Create a memory-anchored query."""
        return cls.MEMORY_ANCHOR.format(
            topic=topic, summary=summary[:200], new_query=new_query
        )
