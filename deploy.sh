#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to get the current version from pyproject.toml
get_current_version() {
    if [ -f "pyproject.toml" ]; then
        grep "^version = " pyproject.toml | cut -d'"' -f2
    else
        echo "0.0.0"
    fi
}

# Function to update version in pyproject.toml
update_version() {
    local new_version=$1
    if [ -f "pyproject.toml" ]; then
        sed -i '' "s/^version = .*/version = \"$new_version\"/" pyproject.toml
    else
        print_error "pyproject.toml not found"
    fi
}

# Function to increment version
increment_version() {
    local version=$1
    if [ -z "$version" ] || [ "$version" = "0.0.0" ]; then
        echo "0.0.1"
        return
    fi
    
    # Split version into major, minor, patch
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    local patch=$(echo "$version" | cut -d. -f3)
    
    # Increment patch version
    patch=$((patch + 1))
    
    # Return new version
    echo "$major.$minor.$patch"
}

# Ensure we're in the right directory
cd "$(dirname "$0")" || print_error "Could not change to script directory"

# Show git history with versions
echo "Recent version history:"
git log --oneline --decorate --all | head -n 10

# Ask if user wants to continue or exit
read -p "Continue with deployment? (y/n): " continue_deploy
if [ "$continue_deploy" != "y" ]; then
    print_status "Deployment cancelled"
    exit 0
fi

# Get commit message from user
read -p "Enter commit message: " COMMIT_MESSAGE
if [ -z "$COMMIT_MESSAGE" ]; then
    print_error "Commit message cannot be empty"
fi

# Get current version from pyproject.toml and suggest next version
CURRENT_VERSION=$(get_current_version)
SUGGESTED_VERSION=$(increment_version "$CURRENT_VERSION")
print_status "Current version (from pyproject.toml): $CURRENT_VERSION"
print_status "Suggested next version: $SUGGESTED_VERSION"

# Get version from user
read -p "Enter version number [$SUGGESTED_VERSION]: " VERSION
VERSION=${VERSION:-$SUGGESTED_VERSION}

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format. Please use semantic versioning (e.g., 1.0.0)"
fi

# Update version in pyproject.toml
print_status "Updating version in pyproject.toml..."
update_version "$VERSION"

# Check if we have uncommitted changes
print_status "Checking for changes..."
if [ -n "$(git status --porcelain)" ]; then
    # Add all changes
    print_status "Adding changes..."
    git add .

    # Commit with the provided message
    print_status "Committing changes..."
    git commit -m "$COMMIT_MESSAGE" || print_error "Failed to commit changes"

    # Create version tag
    print_status "Creating version tag v$VERSION..."
    git tag -a "v$VERSION" -m "Version $VERSION: $COMMIT_MESSAGE" || print_error "Failed to create tag"

    # Push to the default branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    print_status "Pushing to remote branch $BRANCH..."
    
    # Check if branch has upstream
    if git rev-parse --abbrev-ref "@{upstream}" >/dev/null 2>&1; then
        git push || print_error "Failed to push changes"
    else
        git push --set-upstream origin "$BRANCH" || print_error "Failed to push changes"
    fi

    # Push tags
    print_status "Pushing tags..."
    git push --tags || print_error "Failed to push tags"

    print_status "Deployment complete! Version v$VERSION has been released."
else
    print_warning "No changes to deploy"
fi
