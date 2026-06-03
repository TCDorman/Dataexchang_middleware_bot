from src.profiles.profile_detector import ProfileDetector

detector = ProfileDetector()

profile_name = detector.detect_profile(
    "data/customer_input/ford_profile_orders.csv"
)

print(profile_name)