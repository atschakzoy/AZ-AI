output "foundry_endpoint" {
  value = module.foundry-tools.endpoint
}

output "content-safety" {
  value = module.content-safety.endpoint
}

output "cv_training_endpoint" {
  value = module.computer-vision.training_endpoint
}

output "cv_training_key" {
  value     = module.computer-vision.training_key
  sensitive = true
}

output "cv_prediction_endpoint" {
  value = module.computer-vision.prediction_endpoint
}

output "cv_prediction_key" {
  value     = module.computer-vision.prediction_key
  sensitive = true
}

output "cv_prediction_resource_id" {
  value = module.computer-vision.prediction_resource_id
}

output "face_endpoint" {
  value = module.face-api.face_endpoint
}

output "face_key" {
  value     = module.face-api.face_key
  sensitive = true
}

output "translator_endpoint" {
  value = module.translator.endpoint
}

output "translator_key" {
  value     = module.translator.key
  sensitive = true
}

output "translator_region" {
  value = module.translator.region
}

output "speech_endpoint" {
  value = module.speech.endpoint
}

output "speech_key" {
  value     = module.speech.key
  sensitive = true
}

output "speech_region" {
  value = module.speech.region
}

output "di_endpoint" {
  value = module.document-intelligence.endpoint
}

output "di_key" {
  value     = module.document-intelligence.key
  sensitive = true
}

output "search_endpoint" {
  value = module.search.endpoint
}

output "search_key" {
  value     = module.search.key
  sensitive = true
}

output "storage_connection_string" {
  value     = module.storage.connection_string
  sensitive = true
}

output "storage_container_name" {
  value = module.storage.container_name
}

output "storage_account_name" {
  value = module.storage.account_name
}

