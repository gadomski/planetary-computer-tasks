
module "batch_pool_d3_v3" {
  source = "../batch_pool"

  name                = var.batch_default_pool_id
  resource_group_name = module.resources.resource_group
  account_name        = module.resources.batch_account_name
  display_name        = "D v3 family four core"
  vm_size             = "STANDARD_D3_V2"
  max_tasks_per_node  = 4
  # max_tasks_per_node  = 1

  min_dedicated = 0
  max_dedicated = 0

  min_low_priority = var.min_low_priority
  max_low_priority = 50

  max_increase_per_scale = 50

  acr_name = var.task_acr_name
  acr_client_id = var.task_acr_sp_client_id
  acr_client_secret = var.task_acr_sp_client_secret

  subnet_id = module.resources.batch_nodepool_subnet
}

module "batch_pool_d3_v3_ingest" {
  source = "../batch_pool"

  name                = "ingest_pool"
  resource_group_name = module.resources.resource_group
  account_name        = module.resources.batch_account_name
  display_name        = "D v3 family four core"
  vm_size             = "STANDARD_D3_V2"
  max_tasks_per_node  = 1

  min_dedicated = 0
  max_dedicated = 0

  min_low_priority = var.min_low_priority
  max_low_priority = 1

  max_increase_per_scale = 1

  acr_name = var.task_acr_name
  acr_client_id = var.task_acr_sp_client_id
  acr_client_secret = var.task_acr_sp_client_secret

  subnet_id = module.resources.batch_nodepool_subnet
}
