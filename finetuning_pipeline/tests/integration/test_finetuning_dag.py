import pytest
from airflow.models.dagbag import DagBag

@pytest.mark.integration
def test_dag_loads_with_no_errors():
    """Checks if the DAG file is syntactically correct and can be parsed by Airflow."""
    dagbag = DagBag(dag_folder='dags/', include_examples=False)
    assert not dagbag.import_errors
    assert 'embedding_model_finetuning' in dagbag.dags

# A more advanced integration test would use the Airflow API to trigger the DAG
# in a test environment and check its final state.
# from airflow.api.client.local_client import Client
#
# def test_dag_run_completes():
#     client = Client(None, None)
#     result = client.trigger_dag(dag_id='embedding_model_finetuning')
#     # ... poll for completion status ...
#     assert result['state'] == 'success'