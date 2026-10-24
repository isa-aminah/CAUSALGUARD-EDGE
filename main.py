
from storage.database import initialize_database


def main():
    print("=" * 45)
    print("       CAUSALGUARD-EDGE")
    print(" Pedestrian Safety Analysis System")
    print("=" * 45)

    initialize_database()

    print("Project foundation is ready.")


if __name__ == "__main__":
    main()
