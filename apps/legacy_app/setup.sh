#!/bin/bash


# Step 1: Install dependencies with Poetry
echo "Starting poetry install..."
if poetry install; then
  echo "Poetry install completed successfully."
else
  echo "Poetry install failed. Exiting."
  exit 1
fi

# Step 2: Install pre-commit hooks
echo "Installing pre-commit hooks..."
if pre-commit install; then
  echo "Pre-commit hooks installed successfully."
else
  echo "Pre-commit hook installation failed. Exiting."
  exit 1
fi

# Step 3: Activate poetry environment
echo "Starting poetry shell..."
if poetry shell; then
  echo "Poetry shell activated successfully."
else
  echo "Poetry shell activation failed. Exiting."
  exit 1
fi


echo "Setup completed successfully."
exit 0
