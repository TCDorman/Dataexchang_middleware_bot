from pathlib import Path


# ==================================================
# Customer Profile Discovery
# ==================================================
def get_available_customers(
    profiles_dir: str = "configs/customers",
):
    """
    Read the customer profile folder and return a list
    of possible customer names.

    Example:
    ford_profile.json -> ford
    acme.json         -> acme
    """
    profile_path = Path(profiles_dir)

    if not profile_path.exists():
        return []

    customers = []

    for file in profile_path.iterdir():
        if file.is_file() and file.suffix.lower() == ".json":
            customer_name = file.stem.lower()

            # Normalize profile filenames like ford_profile.json
            if customer_name.endswith("_profile"):
                customer_name = customer_name.replace("_profile", "")

            customers.append(customer_name)

    return sorted(set(customers))


# ==================================================
# Detect Customer From File Names
# ==================================================
def detect_customer_from_files(file_paths):
    """
    Attempt to detect the customer by checking whether
    a known customer name appears in the incoming file names.

    Example:
    ford_pair_headers.csv -> Ford
    acme_orders.csv       -> Acme
    """
    customers = get_available_customers()

    file_names = [
        Path(file_path).name.lower()
        for file_path in file_paths
    ]

    for customer in customers:
        for file_name in file_names:
            if customer in file_name:
                return customer.title()

    return None