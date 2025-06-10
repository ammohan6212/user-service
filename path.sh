#!/bin/bash

# Exit if any command fails
set -e

# Push your current changes first
git push origin $(git rev-parse --abbrev-ref HEAD)

# Add submodule (only if not already added)
git submodule add https://github.com/ammohan6212/jenkins-common.git jenkins-common || true

# Initialize submodule
git submodule update --init --recursive

# Switch submodule to desired branch (main or master)
cd jenkins-common
git checkout main  # or master or whichever branch has files
git pull
cd ..

# Copy contents of submodule to current directory
cp -r jenkins-common/* . || true
cp -r jenkins-common/.[!.]* . 2>/dev/null || true  # copy hidden files, skip . and ..

# Remove submodule from Git tracking
git rm -f jenkins-common

# Clean up .gitmodules and config
rm -rf .git/modules/jenkins-common
sed -i '/jenkins-common/d' .gitmodules 2>/dev/null || true
sed -i '/jenkins-common/d' .git/config 2>/dev/null || true

# Clean up directory
rm -rf jenkins-common

# Add and commit updated state
git add -A
git commit -m "Flatten submodule into main directory"
git push origin $(git rev-parse --abbrev-ref HEAD)
