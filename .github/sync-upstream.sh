#!/bin/bash
# Helper script to sync from upstream and clean up unwanted workflows

set -e

echo "Fetching from upstream..."
git fetch upstream

echo "Merging upstream/main into current branch..."
git merge upstream/main

echo "Cleaning up unwanted workflow files..."
cd "$(git rev-parse --show-toplevel)/.github/workflows"

# List of workflows to keep
KEEP_FILES=(
    "test-docker-build.yaml"
    "deploy.yaml"
)

# Remove all workflow files except the ones we want to keep
for file in *.yaml *.yml; do
    if [[ -f "$file" ]]; then
        keep=false
        for keep_file in "${KEEP_FILES[@]}"; do
            if [[ "$file" == "$keep_file" ]]; then
                keep=true
                break
            fi
        done

        if [[ "$keep" == false ]]; then
            echo "Removing unwanted workflow: $file"
            rm -f "$file"
        fi
    fi
done

echo "Cleanup complete. Only keeping: ${KEEP_FILES[*]}"
echo ""
echo "If any workflows were removed, commit the changes:"
echo "  git add .github/workflows/"
echo "  git commit -m 'chore: remove unwanted workflows after upstream sync'"
