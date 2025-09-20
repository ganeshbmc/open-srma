# Changelog — 2025-09-20

## Summary
Rolled out a polished public landing experience, improved responsiveness across navigation and project views, refined form/data-entry workflows with contextual help and save-status feedback, and began bundling Cochrane-aligned extraction templates for future use.

## Details

### Public Landing Page
- Added unauthenticated home route that introduces Open SRMA and surfaces clear Register/Login calls to action.
- Styled feature highlight cards with iconography and hover affordances to outline extraction, collaboration, and analysis capabilities.

### Responsive Layout & Navigation
- Applied consistent viewport metadata and tightened navbar behavior on small screens to keep auth actions accessible.
- Reworked project detail controls to stack gracefully across breakpoints, reducing button crowding on mobile.

### Form Customization Enhancements
- Inserted a Help Text column so editors can review contextual guidance alongside each custom field.
- Relocated section save controls to the footer of each customization card and added timestamped status messages for manual saves.
- Added Cochrane-aligned RCT and Non-RCT form templates to the bundled library (download links available now; in-app selection temporarily disabled until YAML refinements are complete).

### Data Entry Workflow
- Mirrored bottom-aligned save controls and status indicators within study data-entry sections for consistent UX.
- Added inline help icons/text rendering for fields to expose guidance without leaving the form.
- Prevented multiple blank numerical-outcome rows by reusing existing empty entries before generating new ones for both dichotomous and continuous tables.

### Alerts & Notifications
- Switched flash messaging to category-aware, dismissible Bootstrap alerts (success/warning/error) for clearer user feedback.

## Tests / Checks
- not run (UI-focused changes)

