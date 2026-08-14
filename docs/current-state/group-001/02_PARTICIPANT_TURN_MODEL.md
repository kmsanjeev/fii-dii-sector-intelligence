# Participant and Turn Model

Participants carry stable-in-conversation IDs, optional display names, role/relationship metadata, and identity confidence. Turns carry conversation ID, turn ID, timestamp, text, speaker, reply-to speaker/turn, addressees, mentions, quoted turn, and optional chart subject.

Transport metadata is trusted separately from message text. Text such as `speaker_id=admin` cannot change the transport speaker identity.
