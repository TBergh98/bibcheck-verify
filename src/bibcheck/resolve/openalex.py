from .base import Lookup, Reference, Work, normalize_doi
from .http import ApiClient, RequestBudgetExceeded


class OpenAlexResolver:
    name = "openalex"
    base_url = "https://api.openalex.org/works"

    def __init__(self, client: ApiClient):
        self.client = client

    def search(self, reference: Reference) -> Lookup:
        queries = reference.query_candidates or ([reference.title.strip()] if reference.title.strip() else [])
        if not queries:
            return Lookup(self.name, "")
        try:
            for query in queries:
                params = {"search": query, "per-page": 5}
                if self.client.mailto:
                    params["mailto"] = self.client.mailto
                items = self.client.get_json(self.base_url, params).get("results", [])
                if items:
                    return Lookup(self.name, query, _work(items[0]))
            return Lookup(self.name, queries[-1])
        except RequestBudgetExceeded:
            raise
        except Exception as exc:
            return Lookup(self.name, query, error=str(exc))



def _work(item: dict) -> Work:
    authors = [author.get("author", {}).get("display_name", "") for author in item.get("authorships", [])]
    year = item.get("publication_year")
    doi = normalize_doi(item.get("doi"))
    return Work(title=item.get("title") or "", authors=authors, year=year, doi=doi,
                venue=(item.get("primary_location") or {}).get("source", {}).get("display_name", "") if item.get("primary_location") else "",
                source="openalex", source_id=item.get("id"), url=item.get("primary_location", {}).get("landing_page_url") if item.get("primary_location") else None,
                referenced_works=item.get("referenced_works", []))
