"""Registry of built-in skills that SID can learn/download."""
BUILTIN_SKILLS = {
    "web_search": {
        "name": "Web Search",
        "version": "1.2.0",
        "description": "Search the internet and retrieve web content",
        "url": "",
        "requires": ["network"],
        "provides": ["web_search", "web_scrape", "link_extract"]
    },
    "image_generation": {
        "name": "Image Generation",
        "version": "1.2.0",
        "description": "Generate images using stable diffusion or API",
        "url": "",
        "requires": ["model:stable-diffusion"],
        "provides": ["text_to_image", "image_variation"]
    },
    "data_analysis": {
        "name": "Data Analysis",
        "version": "1.2.0",
        "description": "Analyze and visualize data",
        "url": "",
        "requires": ["python:pandas"],
        "provides": ["analyze", "visualize", "summarize"]
    },
    "file_conversion": {
        "name": "File Conversion",
        "version": "1.2.0",
        "description": "Convert between file formats",
        "url": "",
        "requires": ["pandoc", "imagemagick"],
        "provides": ["convert", "compress", "extract"]
    },
    "network_diagnostics": {
        "name": "Network Diagnostics",
        "version": "1.2.0",
        "description": "Diagnose network issues",
        "url": "",
        "requires": ["ping", "traceroute"],
        "provides": ["ping_test", "trace_route", "dns_lookup"]
    },
    "system_optimization": {
        "name": "System Optimization",
        "version": "1.2.0",
        "description": "Deep system optimization",
        "url": "",
        "requires": ["sudo"],
        "provides": ["optimize_ram", "clean_disk", "update_all"]
    },
    "security_audit": {
        "name": "Security Audit",
        "version": "1.2.0",
        "description": "Security auditing",
        "url": "",
        "requires": ["nmap"],
        "provides": ["port_check", "vuln_scan", "audit_system"]
    },
    "crypto_tools": {
        "name": "Crypto Tools",
        "version": "1.2.0",
        "description": "Encryption, hashing, and signing",
        "url": "",
        "requires": ["openssl"],
        "provides": ["encrypt", "decrypt", "hash", "sign"]
    }
}
