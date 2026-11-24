{
  "type": "object",
  "required": ["role_arns", "duration_seconds", "cert_common_name", "cert_validity_days"],
  "properties": {
    "role_arns": { "type": "array", "items": { "type": "string", "pattern": "^arn:aws:iam::[0-9]{12}:role/.+" } },
    "duration_seconds": { "type": "integer", "maximum": 3600 },
    "cert_common_name": { "type": "string" },
    "cert_validity_days": { "type": "integer", "maximum": 7 }
  },
  "additionalProperties": false
}
