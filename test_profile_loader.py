from src.profiles.profile_loader import ProfileLoader

loader = ProfileLoader()

profile = loader.load_profile("ford")

print(profile)