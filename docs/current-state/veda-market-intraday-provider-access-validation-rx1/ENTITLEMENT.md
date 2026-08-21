# Entitlement

The authenticated Dhan profile returned HTTP 200 and reported:

- authenticated client: present;
- active segments: `E, D, C, M`;
- Data API plan: `Deactive`;
- data validity: `NA`.

The historical endpoint returned provider error `DH-902`, which the runtime
normalizes to `DATA_ENTITLEMENT_REQUIRED`. Quote and option requests are also
blocked under the same known inactive-plan state. Authentication therefore
must not be reported as market-data entitlement.
