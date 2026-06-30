# Attachments

This starter uses content-addressed attachment storage. Each attachment record stores filename, media type, size, SHA256, storage path, and source id. Generated bundles cite SHA256 metadata instead of duplicating file contents.

For private use, keep large/private attachments out of Git and commit only metadata if that fits your privacy model.
