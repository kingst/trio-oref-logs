# OpenAPS Algorithm Validation API

## Overview The OpenAPS Algorithm Validation API enables automated
collection and storage of algorithm comparison data between Javascript
and native Swift implementations of the OpenAPS Oref algorithms.

## Base URL
```
https://trio-oref-logs.uc.r.appspot.com
```

## Endpoints

### Get Signed URL
Generates a signed URL for uploading algorithm comparison data to Google Cloud Storage.

#### Request
`POST /v1/signed-url`

##### Headers
```
Content-Type: application/json
```

##### Body Parameters
| Parameter   | Type   | Required | Description |
|------------|--------|----------|-------------|
| project    | string | Yes      | Project identifier (e.g., "oref-validation") |
| deviceId   | string | Yes      | iOS Vendor ID for device identification |
| appVersion | string | Yes      | Semantic version of the app (e.g., "2.1.3") |
| function   | string | Yes      | Algorithm function being compared |
| createdAt  | number | Yes      | Unix timestamp in seconds.milliseconds |

##### Supported Functions
- `determineBasal`
- `autosense`
- `makeProfile`
- `meal`
- `iob`

##### Example Request
```json
{
    "project": "trio-oref-validation",
    "deviceId": "1234ABCD-EFGH-5678",
    "appVersion": "2.1.3",
    "function": "determineBasal",
    "createdAt": 1707235200.453
}
```

#### Response

##### 200 Success
```json
{
    "url": "https://storage.googleapis.com/oref-validation/algorithm-comparisons/2025-02-06/2.1.3/determineBasal/1234ABCD-EFGH-5678/550e8400-e29b-41d4-a716-446655440000.json?X-Goog-Algorithm=...",
    "expiresAt": 1707236100.000
}
```

| Field     | Type   | Description |
|-----------|--------|-------------|
| url       | string | Signed URL for uploading data |
| expiresAt | number | Unix timestamp when URL expires |

##### Error Responses

###### 400 Bad Request
- Missing required fields
- Invalid function name
- Malformed JSON

###### 500 Internal Server Error
- Storage service errors
- Server configuration issues

## Storage Structure

### GCS Path Format
```
{project}/algorithm-comparisons/{date}/{app_version}/{function}/{device_id}/{batch_id}.json
```

### Path Components

| Component    | Format    | Example    | Description |
|-------------|-----------|------------|-------------|
| project     | string    | oref-validation | Project identifier |
| date        | YYYY-MM-DD| 2025-02-06 | UTC date from createdAt |
| app_version | semver    | 2.1.3      | Application version |
| function    | string    | determineBasal | Algorithm function |
| device_id   | UUID      | 1234ABCD-EFGH-5678 | iOS Vendor ID |
| batch_id    | UUID      | 550e8400-... | Server-generated batch ID |

### Example Full Paths
```
oref-validation/algorithm-comparisons/2025-02-06/2.1.3/determineBasal/1234ABCD-EFGH-5678/550e8400-e29b-41d4-a716-446655440000.json
oref-validation/algorithm-comparisons/2025-02-06/2.1.3/makeProfile/1234ABCD-EFGH-5678/98765432-abcd-efgh-ijkl-123456789012.json
```

## Notes
- All timestamps are in UTC
- URLs expire 15 minutes after generation
- Maximum upload size: 10MB per batch
- JSON is the only supported upload format
