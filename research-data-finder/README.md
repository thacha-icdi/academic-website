# Research Data Finder

Live website: https://thacha-icdi.github.io/academic-website/research-data-finder/

Buildless HTML/CSS/JavaScript application hosted on GitHub Pages.

## Use
1. Enter English research keywords and optionally a minimum publication year.
2. Search live DataCite dataset DOI metadata (20 records per page).
3. Open the dataset landing page or DOI to inspect access, variables, methodology and license.
4. Save records to a browser-local shortlist; open Saved and export CSV.
5. Expand external sources to search Kaggle, UCI, Zenodo, Harvard Dataverse, Hugging Face, Thailand Open Data and Google Dataset Search separately.

## Data and limitations
Public API: https://api.datacite.org/dois
Documentation: https://support.datacite.org/docs/rest-api

No API key or server is required. Live requests require internet access and depend on provider availability and browser CORS policy. API errors are shown explicitly without fabricated sample results. DOI records are not a guarantee of open access, quality, representativeness, or ethical suitability. External source results are not aggregated into the DataCite list. Saved records persist only in the current browser profile and can be lost if storage is cleared. CSV exports only the current results page or the complete saved shortlist, depending on the selected view. CSV cells are escaped and formula-leading values are neutralized.

## Editing
Edit research-data-finder/index.html on the main branch. Existing GitHub Pages deployment publishes the folder. No dependency installation or build step is needed.

Created by Assoc. Prof. Dr. Thacha Lawanna.
