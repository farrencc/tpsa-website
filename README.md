# TPSA Website - Webmaster Guide

The official website for the Theoretical Physics Student Association (TPSA) of Ireland and The Problem Solving Association CLG. 

The site uses a template-based architecture with reusable header and footer components to wrap around page content. This approach generates static HTML pages from modular components - `header.html`, `footer.html`, and `<name>-body.html` to compile the website. There also a handful of other unique pages such as the `index.html` & `problem-solving.html`. 

# Table of Contents

1. ***Project Structure***
2. ***Quick Start***
3. ***The Build Script***
4. ***Deployment***
5. ***Troubleshooting***
6. ***Copyright***


# Project Structure

```
├── site/                   # Generated files + assets (this gets deployed)
│   ├── .htaccess           # Url rerouting
│   ├── tpsa.css            # Main stylesheet (edit directly)
│   ├── tpsa.js             # JavaScript functions
│   ├── index.html          # Unique page (edit directly)
│   ├── problem-solving.html# Unique page (edit directly)
│   └── *.html              # Generated pages (DON'T edit these directly)
├── content/                # Page content (edit these)
│   ├── student-body.html   # Becomes student.html
│   ├── projects-body.html  # Becomes projects.html
│   ├── committee-body.html # Becomes committee.html
│   ├── history-body.html   # Becomes history.html
│   ├── internships-body.html # Becomes internships.html
│   └── sign-up-body.html   # Becomes sign-up.html
├── templates/              # Site structure (edit these)
│   ├── header.html         # Navigation, <head>, opening <body>
│   └── footer.html         # Footer, closing </body></html>
└── tpsa.sh                 # Build script
```


# Quick Start

1. **Edit content** in `content/` and `templates/` directories
2. **Test locally** by running `./tpsa.sh server` with `venv` (view at localhost:8000)
3. **Commit and push** to a feature branch for review
4. **Merge to main** - GitHub Actions will automatically build and deploy to tpsa.ie


# Build Script

The `tpsa.sh` script is the heart of the build system:

## How it works:
```
header.html + [content]-body.html + footer.html = [content].html
```
- Takes each `*-body.html` file from `content/`
- Wraps it with `templates/header.html` and `templates/footer.html`
- Outputs the complete page to `site/*.html`

## Usage:
```bash
# Build all pages
./tpsa.sh

# Build and start development server at localhost:8000
./tpsa.sh server

# Build specific page only
./tpsa.sh <name>    # Only builds student<name>.html
```

# Development 

## 1. First Time Setup
```
# Clone the repository
git clone https://github.com/ciangregg/tpsa-website.git
cd tpsa-website

# Set up Python virtual environment (if it doesn't exist)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Test the build system
./tpsa.sh server
```

## 2. Editing Content

### Which Files to Edit
#### For Page Content

`content/student-body.html` → becomes `student.html`
`content/*-body.html` → becomes `*.html`


#### For Site-wide Changes

`templates/header.html` - Navigation, metadata, opening tags
`templates/footer.html` - Footer content, closing tags

#### For Unique Pages

`site/index.html` - Split landing page
`site/problem-solving.html` - The Problem Solving Association page

#### For Styling and Functionality

site/tpsa.css - All website styling
site/tpsa.js - Interactive functions and popups

## Testing
Run the build script and test your changes
```
./tpsa.sh server
```

## Git Workflow
```
# Create and switch to a new feature branch
git checkout -b feature-branch

# Make your changes...
# Test locally with ./tpsa.sh server

# Stage and commit your changes
git add .
git commit -m "Updates...."

# Push to remote repository
git push origin feature-branch

# Create Pull Request on GitHub for review
# Merge to main once approved
```

## Deployment to **_tpsa.ie_** 
The site uses automated deployment through GitHub Actions. When you push changes to the main branch, GitHub Actions automatically triggers the build process runs - `.github/workflows/build-deploy.yml`,
The Action runs `tpsa.sh` to generate all pages, validates the build, and deploys everything to the production branch. Plesk then automatically pulls these changes and updates tpsa.ie, with the entire process usually taking 2-3 minutes from push to live site, _hopefully_. 


# Troubleshooting
### Changes not loading? 
Clear the cache of your testing browers to make sure nothing is cached, `shift+ctrl+delete`

...


# Copyright

© 2025 Theoretical Physics Student Association of Ireland. All rights reserved.