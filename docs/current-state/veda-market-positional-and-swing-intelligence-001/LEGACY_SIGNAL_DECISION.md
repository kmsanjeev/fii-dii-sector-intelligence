# Legacy signal decision

The new contract does not import or call the legacy conviction/recommender
engines. Existing files are preserved for historical/experimental compatibility
and are explicitly marked as excluded in provider provenance. Their scores do
not become evidence merely because they exist in the data directory.
