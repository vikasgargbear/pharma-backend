# Configuration Directory

This directory contains environment-specific configuration files.

## Structure

- `development/` - Development environment settings
- `production/` - Production environment settings  
- `testing/` - Test environment settings

## Usage

Configuration files should be loaded based on the `ENVIRONMENT` variable:
- `ENVIRONMENT=development` - Uses development config
- `ENVIRONMENT=production` - Uses production config
- `ENVIRONMENT=testing` - Uses testing config

## Security

- Never commit sensitive data (API keys, passwords) to these files
- Use environment variables or secret management systems
- `.env` files should be in `.gitignore`