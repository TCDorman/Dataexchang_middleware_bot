from src.profiles.profile_registry import (
    ProfileRegistry
)

registry = ProfileRegistry()

profiles = registry.get_profiles()

print(profiles.keys())