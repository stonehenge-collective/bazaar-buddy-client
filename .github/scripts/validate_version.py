import json, sys, os, re


def main():

    tag_version = os.getenv("GITHUB_REF_NAME")

    # Validate version format: vn.n.n or vn.n.n-test
    version_pattern = r"^v\d+\.\d+\.\d+(-test)?$"

    if not re.match(version_pattern, tag_version):
        print(f"Invalid tag format: {tag_version}")
        print("Expected format: vx.x.x or vx.x.x-test")
        return 1

    with open(os.path.join(sys.path[0], "..", "..", "configuration.json"), "r") as f:
        configuration = json.load(f)
        configuration_version = configuration["version"]
        if not configuration_version:
            print("failed to load configuration.json")
            return 1

    if not re.match(version_pattern, configuration_version):
        print(f"Invalid config version format: {configuration_version}")
        print("Expected format: vx.x.x or vx.x.x-test")
        return 1

    if tag_version is None:
        print("failed to pull tag from runner environment")
        return 1

    if configuration_version != tag_version:
        print(
            f"Version mismatch! Version in configuration.json ({configuration_version}) != pushed tag ({tag_version})"
        )
        return 1

    is_test_release = tag_version.endswith("-test")

    if is_test_release:
        if not configuration["update_with_test_release"]:
            print(
                f"pushed tag ({tag_version}) is a test release, but update_with_test_release is false in configuration.json"
            )
            return 1
    else:
        if configuration["update_with_test_release"]:
            print(
                f"pushed tag ({tag_version}) is a non-test release, but update_with_test_release is true in configuration.json"
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
