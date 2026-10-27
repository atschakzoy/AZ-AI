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