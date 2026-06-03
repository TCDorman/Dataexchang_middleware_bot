from src.profiles.profile_detector import ProfileDetector

detector = ProfileDetector()

profile = detector.detect_profile(
    "data/customer_input/ford_profile_orders.csv"
)

print(profile)