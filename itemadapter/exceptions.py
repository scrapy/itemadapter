class NoMetadataSupport(TypeError):
    """
    Raised when ItemAdapter.get_field_meta is called
    on an item that does not support metadata.
    """
