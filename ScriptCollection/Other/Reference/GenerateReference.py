from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore


def generate_reference():
    ScriptCollectionCore().standardized_tasks_generate_reference_by_docfx(__file__)


if __name__ == "__main__":
    generate_reference()
