import logging
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from opensearchpy.helpers import bulk

logger = logging.getLogger(__name__)

def get_opensearch_client(host: str, region: str):
    """Initializes and returns an OpenSearch client."""
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, 'aoss')
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20
    )
    return client

def index_documents(client: OpenSearch, index_name: str, documents: List[dict]):
    """Bulk indexes documents into OpenSearch."""
    logger.info(f"Indexing {len(documents)} documents into index '{index_name}'.")
    success, failed = bulk(client, documents, index=index_name)
    if failed:
        logger.error(f"Failed to index {len(failed)} documents.")
    return success, failed