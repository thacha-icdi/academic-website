# Keyword Dataset Finder

Website: https://thacha-icdi.github.io/academic-website/research-data-finder/

Enter a keyword and click Find. The app matches against a small verified UCI catalogue and searches Hugging Face's public dataset API live. It inspects file listings for up to 24 public ungated repositories, with four concurrent requests, and displays up to ten matching datasets that have CSV, JSON/JSONL or Excel files. Fewer than ten results is a valid outcome. No unrelated examples are used as fallback.

UCI matching uses all normalized keyword tokens against curated titles and topic keywords. Hugging Face matching follows the provider search API. File formats are identified from file names, not downloaded contents. File names cannot guarantee data quality, contents, license compatibility or accessibility. Known metadata JSON names are excluded. Live requests time out after 25 seconds. Failures and inaccessible repositories are reported. Coverage is limited to the UCI catalogue and Hugging Face; this is not a universal dataset search engine.

External source search links remain available for UCI, Kaggle, Hugging Face, Google Dataset Search, Thailand Open Data and Zenodo. They are clearly separate from matched results. The matching-source section lists only repositories represented by displayed dataset matches.

Changing the keyword clears previous results and cancels pending requests. Clear empties the field and hides results. Empty input shows no recommendations.

Buildless HTML/CSS/JavaScript hosted on GitHub Pages. No API keys or dependencies. Edit index.html to update the website.
