from .base import Lookup, Reference, Work, normalize_doi
from .http import ApiClient, RequestBudgetExceeded


class CrossrefResolver:
    name = "crossref"
    base_url = "https://api.crossref.org"

    def __init__(self, client: ApiClient):
        self.client = client

    def resolve_doi(self, reference: Reference) -> Lookup:
        doi = normalize_doi(reference.doi_if_present) or ""
        try:
            item = self.client.get_json(f"{self.base_url}/works/{doi}").get("message", {})
            work = _work(item)
            return Lookup(self.name, doi, work, 1.0, normalize_doi(work.doi) == doi)
        except RequestBudgetExceeded:
            raise
        except Exception as exc:
            return Lookup(self.name, doi, error=str(exc))

    def search(self, reference: Reference) -> Lookup:
        queries = reference.query_candidates or ([reference.title.strip()] if reference.title.strip() else [])
        if not queries:
            return Lookup(self.name, "")
        try:
            for query in queries:
                items = self.client.get_json(f"{self.base_url}/works", {"query.bibliographic": query, "rows": 5}).get("message", {}).get("items", [])
                if items:
                    return Lookup(self.name, query, _work(items[0]))
            return Lookup(self.name, queries[-1])
        except RequestBudgetExceeded:
            raise
        except Exception as exc:
            return Lookup(self.name, query, error=str(exc))


def _work(item: dict) -> Work:
    authors = [" ".join(filter(None, (author.get("given", ""), author.get("family", "")))) for author in item.get("author", [])]
    year_values = item.get("published", {}).get("date-parts", [[]])[0]
    return Work(title=(item.get("title") or [""])[0], authors=authors,
                year=year_values[0] if year_values else None, doi=item.get("DOI"),
                venue=(item.get("container-title") or [""])[0], source="crossref",
                source_id=item.get("DOI"), url=item.get("URL"))
