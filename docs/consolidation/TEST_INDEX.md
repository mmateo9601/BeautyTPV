# Indice de pruebas de consolidacion

Definiciones comprobables; el resultado efectivo y parametrizaciones estan en JUnit. Las matrices obligatorias agrupan requisitos por operacion y referencian estos archivos.

## tests/e2e/test_audit_acceptance.py

- [test_superadmin_terminal_printer_and_fiscal_configuration_forms](../../tests/e2e/test_audit_acceptance.py#L80)
- [test_superadmin_creates_encrypted_backup_and_prepares_offline_restore](../../tests/e2e/test_audit_acceptance.py#L120)

## tests/e2e/test_audit_ui.py

- [test_pending_payment_blocks_editing_and_retains_note](../../tests/e2e/test_audit_ui.py#L12)
- [test_role_navigation_and_mobile_layout](../../tests/e2e/test_audit_ui.py#L49)

## tests/e2e/test_browser.py

- [test_e01_browser_pin_cash_invoice_copy_report_and_close](../../tests/e2e/test_browser.py#L106)
- [test_e02_browser_accounts_survive_navigation_and_new_browser_session](../../tests/e2e/test_browser.py#L157)
- [test_e03_e16_browser_catalog_customer_full_invoice_and_snapshot](../../tests/e2e/test_browser.py#L193)

## tests/e2e/test_consolidation_ui.py

- [test_admin_settings_logo_preferences_and_register_crud](../../tests/e2e/test_consolidation_ui.py#L71)
- [test_manager_incident_create_validate_and_resolve](../../tests/e2e/test_consolidation_ui.py#L117)
- [test_superadmin_revokes_user_session_from_team_controls](../../tests/e2e/test_consolidation_ui.py#L149)
- [test_admin_category_visibility_reaches_real_pos_and_cart](../../tests/e2e/test_consolidation_ui.py#L187)

## tests/test_acceptance.py

- [test_e01_cash_sale_invoice_spool_and_closure](../../tests/test_acceptance.py#L69)
- [test_e03_multiple_tax_rates_and_authorized_discount](../../tests/test_acceptance.py#L90)
- [test_e04_mixed_cash_only_component_in_cash_balance](../../tests/test_acceptance.py#L113)
- [test_e06_printer_failure_keeps_sale_and_controlled_copy](../../tests/test_acceptance.py#L127)
- [test_e07_network_loss_does_not_regenerate_fiscal_record](../../tests/test_acceptance.py#L142)
- [test_e08_rejected_correction_preserves_original](../../tests/test_acceptance.py#L161)
- [test_e09_e16_sql_immutability_and_historical_price_snapshot](../../tests/test_acceptance.py#L206)
- [test_e10_e11_roles_reject_backend_privilege_escalation](../../tests/test_acceptance.py#L229)
- [test_e14_card_receipt_never_opens_drawer_software_only](../../tests/test_acceptance.py#L246)
- [test_e11_superadmin_diagnostic_requires_elevation_and_authorization](../../tests/test_acceptance.py#L254)
- [test_e15_rectification_reconciles_cash_and_report](../../tests/test_acceptance.py#L284)
- [test_e15_refund_rechecks_closed_cash_session_from_database](../../tests/test_acceptance.py#L308)

## tests/test_audit_backend.py

- [test_payment_pending_persists_blocks_edits_and_can_checkout](../../tests/test_audit_backend.py#L40)
- [test_prepare_empty_and_conflicting_resume_do_not_lose_account](../../tests/test_audit_backend.py#L57)
- [test_quick_sale_requires_configuration_and_is_reused_per_terminal](../../tests/test_audit_backend.py#L69)
- [test_notes_and_category_filter_are_real_http_to_database](../../tests/test_audit_backend.py#L86)
- [test_post_foreign_keys_are_validated_without_500](../../tests/test_audit_backend.py#L110)
- [test_extreme_money_never_creates_partial_sale](../../tests/test_audit_backend.py#L128)
- [test_checkout_routes_receipt_and_drawer_to_paying_terminal](../../tests/test_audit_backend.py#L137)
- [test_all_critical_services_obey_maintenance](../../tests/test_audit_backend.py#L159)
- [test_sqlite_retry_rolls_back_whole_unit_before_repeat](../../tests/test_audit_backend.py#L178)
- [test_reports_filters_cancellation_and_tax_snapshot](../../tests/test_audit_backend.py#L199)
- [test_replacement_cannot_rewrite_sale_or_closed_ticket](../../tests/test_audit_backend.py#L232)
- [test_sections_and_company_settings_validate_real_admin_changes](../../tests/test_audit_backend.py#L250)
- [test_sum_of_valid_payment_components_cannot_overflow_sale_field](../../tests/test_audit_backend.py#L276)

## tests/test_audit_configuration.py

- [test_health_checks_database_and_reports_supervision](../../tests/test_audit_configuration.py#L17)
- [test_health_database_failure_is_not_a_fake_ok](../../tests/test_audit_configuration.py#L30)
- [test_ui_environment_is_company_mode_and_timezone_is_restored](../../tests/test_audit_configuration.py#L41)
- [test_production_start_without_external_secret_fails_closed](../../tests/test_audit_configuration.py#L54)

## tests/test_audit_fiscal.py

- [test_a_f01_verifier_compares_xml_invoice_and_hash_inputs](../../tests/test_audit_fiscal.py#L38)
- [test_a_f01_verifier_checks_actual_chain_identity](../../tests/test_audit_fiscal.py#L53)
- [test_a_f02_aeat_wait_is_shared_between_different_pending_records](../../tests/test_audit_fiscal.py#L64)
- [test_a_f02_expired_sender_cannot_overwrite_new_lease](../../tests/test_audit_fiscal.py#L83)
- [test_a_f03_production_guard_cannot_be_bypassed_by_test_company](../../tests/test_audit_fiscal.py#L99)
- [test_a_f04_extended_response_status_fits_model_validation](../../tests/test_audit_fiscal.py#L115)
- [test_a_f05_rejected_annulment_stays_an_annulment](../../tests/test_audit_fiscal.py#L123)
- [test_a_f06_invoice_date_and_number_year_follow_snapshot_timezone](../../tests/test_audit_fiscal.py#L139)
- [test_a_f07_bad_cash_session_input_is_a_validation_error_not_500](../../tests/test_audit_fiscal.py#L151)
- [test_a_f08_rejected_record_status_is_refetched_before_correction](../../tests/test_audit_fiscal.py#L162)
- [test_a_f09_sqlite_replace_cannot_rewrite_issued_rows](../../tests/test_audit_fiscal.py#L185)
- [test_a_f10_response_operation_must_match_sent_record](../../tests/test_audit_fiscal.py#L207)
- [test_a_f11_each_record_freezes_its_actual_generating_software_version](../../tests/test_audit_fiscal.py#L217)
- [test_a_f12_accepted_with_errors_uses_subsanacion_without_rechazo](../../tests/test_audit_fiscal.py#L233)
- [test_a_f13_producer_configuration_can_be_corrected_without_rewriting_origin](../../tests/test_audit_fiscal.py#L248)
- [test_a_f03_old_production_outbox_still_requires_approval_after_mode_switch](../../tests/test_audit_fiscal.py#L268)
- [test_technical_annulment_http_preserves_sale_and_records_reason](../../tests/test_audit_fiscal.py#L296)

## tests/test_audit_forms.py

- [test_admin_company_configuration_form_persists_validated_values](../../tests/test_audit_forms.py#L18)
- [test_customer_and_catalog_forms_save_and_preserve_history](../../tests/test_audit_forms.py#L42)
- [test_manager_line_discount_cancellation_movements_and_cash_close](../../tests/test_audit_forms.py#L81)
- [test_manager_cash_refund_from_invoice_form_reconciles_database](../../tests/test_audit_forms.py#L129)
- [test_superadmin_queue_controls_create_real_jobs_and_corrections](../../tests/test_audit_forms.py#L150)
- [test_admin_user_creation_and_pin_change_revoke_logged_in_operator](../../tests/test_audit_forms.py#L177)
- [test_employee_cash_screen_hides_other_employees_closed_sessions](../../tests/test_audit_forms.py#L207)

## tests/test_audit_hardware.py

- [test_tcp_loopback_transmits_exact_bytes_without_physical_device](../../tests/test_audit_hardware.py#L102)
- [test_invalid_device_configuration_rejected](../../tests/test_audit_hardware.py#L145)
- [test_invalid_device_does_not_roll_back_invoice_spooling](../../tests/test_audit_hardware.py#L152)
- [test_full_receipt_contains_customer_and_rectification_reference](../../tests/test_audit_hardware.py#L163)
- [test_print_intent_and_hardware_events_cannot_be_changed_by_queryset](../../tests/test_audit_hardware.py#L174)
- [test_lease_expired_during_send_is_not_falsely_reported_done](../../tests/test_audit_hardware.py#L183)
- [test_retry_different_encoding_is_rejected](../../tests/test_audit_hardware.py#L200)
- [test_bridge_claim_ack_are_token_scoped_and_idempotent](../../tests/test_audit_hardware.py#L214)
- [test_bridge_expired_delivery_is_quarantined_and_remote_jobs_not_locally_sent](../../tests/test_audit_hardware.py#L255)
- [test_bridge_restore_hold_prevents_claim](../../tests/test_audit_hardware.py#L276)
- [test_test_and_retry_endpoints_require_technical_authorization](../../tests/test_audit_hardware.py#L285)
- [test_remote_agent_complete_claim_print_ack_and_restart_safety](../../tests/test_audit_hardware.py#L320)
- [test_agent_rejects_unsafe_server_urls](../../tests/test_audit_hardware.py#L356)
- [test_terminal_routing_prefers_its_device_and_has_explicit_local_fallback](../../tests/test_audit_hardware.py#L362)
- [test_agent_ack_network_failure_retries_ack_without_reprinting](../../tests/test_audit_hardware.py#L386)
- [test_sql_replace_cannot_replace_print_intent_or_hardware_history](../../tests/test_audit_hardware.py#L413)
- [test_multibyte_encoding_cannot_turn_customer_unicode_into_drawer_commands](../../tests/test_audit_hardware.py#L432)

## tests/test_audit_matrix.py

- [test_all_live_routes_and_baseline_have_explicit_audit_policy](../../tests/test_audit_matrix.py#L235)
- [test_every_route_role_authorization](../../tests/test_audit_matrix.py#L253)
- [test_administrative_get_routes_require_elevation](../../tests/test_audit_matrix.py#L286)
- [test_superadmin_pii_needs_an_independent_active_approver](../../tests/test_audit_matrix.py#L299)
- [test_every_visible_menu_link_is_authorized_for_its_role](../../tests/test_audit_matrix.py#L332)
- [test_cookie_authenticated_mutations_reject_missing_csrf](../../tests/test_audit_matrix.py#L353)

## tests/test_audit_ops.py

- [test_partial_file_write_rolls_back_all_code](../../tests/test_audit_ops.py#L54)
- [test_preflight_invalid_destination_never_writes_first_file](../../tests/test_audit_ops.py#L85)
- [test_dependency_mismatch_aborts_before_code_and_backup](../../tests/test_audit_ops.py#L103)
- [test_update_rejects_case_collision_and_unsafe_version](../../tests/test_audit_ops.py#L127)
- [test_release_version_changes_only_after_successful_update](../../tests/test_audit_ops.py#L136)
- [test_supervisor_closes_service_when_child_exits](../../tests/test_audit_ops.py#L151)
- [test_supervisor_reports_monitor_failure](../../tests/test_audit_ops.py#L167)
- [test_certificate_external_references_validate_key_match](../../tests/test_audit_ops.py#L207)
- [test_certificate_must_be_outside_repo](../../tests/test_audit_ops.py#L222)
- [test_invalid_backup_policy_rejected](../../tests/test_audit_ops.py#L230)
- [test_fiscal_failure_does_not_prevent_backup_task](../../tests/test_audit_ops.py#L240)
- [test_revoked_approver_invalidates_support_session](../../tests/test_audit_ops.py#L254)
- [test_terminal_form_hashes_token_and_never_saves_raw_token](../../tests/test_audit_ops.py#L274)
- [test_unlock_user_does_not_require_pin_change](../../tests/test_audit_ops.py#L286)
- [test_printer_form_rejects_unrenderable_encoding_and_invalid_port](../../tests/test_audit_ops.py#L312)

## tests/test_audit_security.py

- [test_pin_reset_revokes_existing_browser_session](../../tests/test_audit_security.py#L17)
- [test_role_change_revokes_existing_elevated_session](../../tests/test_audit_security.py#L27)
- [test_stale_target_does_not_allow_admin_to_edit_new_superadmin](../../tests/test_audit_security.py#L40)
- [test_stale_actor_cannot_keep_permissions_after_demotion](../../tests/test_audit_security.py#L50)
- [test_stale_service_actor_is_revoked_after_credential_reset](../../tests/test_audit_security.py#L57)
- [test_post_account_cannot_bypass_superadmin_pii_guard](../../tests/test_audit_security.py#L65)
- [test_nonfinite_or_boolean_elevation_expiry_is_not_valid](../../tests/test_audit_security.py#L76)
- [test_four_role_url_matrix_with_elevation_and_pii_approval](../../tests/test_audit_security.py#L100)
- [test_privileged_routes_reject_pin_only_superadmin](../../tests/test_audit_security.py#L126)
- [test_pin_only_admin_cannot_access_admin_catalog_or_layout](../../tests/test_audit_security.py#L133)
- [test_security_change_revokes_approver_support_grants](../../tests/test_audit_security.py#L139)
- [test_disable_then_reenable_does_not_resurrect_old_session](../../tests/test_audit_security.py#L158)
- [test_locked_origin_cannot_create_unlimited_account_throttle_rows](../../tests/test_audit_security.py#L167)
- [test_admin_post_requires_csrf_and_logout_is_post_only](../../tests/test_audit_security.py#L179)
- [test_password_forms_preserve_exact_whitespace](../../tests/test_audit_security.py#L190)
- [test_menu_links_follow_role_matrix](../../tests/test_audit_security.py#L203)
- [test_login_validates_terminal_and_clears_previous_assignment](../../tests/test_audit_security.py#L215)
- [test_terminal_context_is_validated_and_does_not_leak_between_requests](../../tests/test_audit_security.py#L237)
- [test_sqlite_replace_cannot_rewrite_audit_evidence](../../tests/test_audit_security.py#L279)
- [test_demotion_clears_inherited_django_superuser_capabilities](../../tests/test_audit_security.py#L298)

## tests/test_backend.py

- [test_bootstrap_is_idempotent_and_no_credentials](../../tests/test_backend.py#L44)
- [test_two_accounts_and_snapshot_persist](../../tests/test_backend.py#L52)
- [test_discount_and_version](../../tests/test_backend.py#L66)
- [test_payment_mixed_idempotent_and_reconciliation](../../tests/test_backend.py#L80)
- [test_invalid_checkout_rolls_back](../../tests/test_backend.py#L103)
- [test_cash_permissions_and_constraints](../../tests/test_backend.py#L120)
- [test_unique_ticket_and_issued_immutability](../../tests/test_backend.py#L138)

## tests/test_backup.py

- [test_backup_encrypted_integrity_and_restore](../../tests/test_backup.py#L47)
- [test_backup_tamper_and_wrong_key_rejected](../../tests/test_backup.py#L62)
- [test_backup_never_overwrites_existing_copy](../../tests/test_backup.py#L76)
- [test_restore_requires_offline_confirmation_and_retains_current](../../tests/test_backup.py#L85)
- [test_service_shared_maintenance_exclusive](../../tests/test_backup.py#L98)
- [test_restore_rejects_running_service](../../tests/test_backup.py#L110)
- [test_update_validates_hash_and_paths](../../tests/test_backup.py#L120)
- [test_update_migrates_without_rollback_database](../../tests/test_backup.py#L133)
- [test_failed_update_rolls_code_back_and_holds_operation](../../tests/test_backup.py#L154)
- [test_support_requires_superadmin_and_elevation](../../tests/test_backup.py#L176)
- [test_support_authorization_scope_expiry_and_pii_separation](../../tests/test_backup.py#L195)
- [test_admin_cannot_create_superadmin_via_team_ui](../../tests/test_backup.py#L231)
- [test_cross_process_worker_blocks_restore](../../tests/test_backup.py#L248)

## tests/test_bootstrap.py

- [test_health](../../tests/test_bootstrap.py#L6)

## tests/test_concurrency.py

- [test_e02_accounts_survive_process_restart](../../tests/test_concurrency.py#L97)
- [test_e05_two_terminals_same_idempotency_key_one_sale](../../tests/test_concurrency.py#L111)
- [test_e05_different_keys_do_not_double_charge_ticket](../../tests/test_concurrency.py#L123)
- [test_e13_three_terminal_sales_numbering_and_chain](../../tests/test_concurrency.py#L133)
- [test_e12_restore_real_issued_database_holds_send_and_preserves_idempotency](../../tests/test_concurrency.py#L149)
- [test_real_process_death_rolls_back_invoice_sequence_and_spool](../../tests/test_concurrency.py#L178)

## tests/test_consolidation_acceptance.py

- [test_logo_rejects_active_malformed_and_oversize_content_atomically](../../tests/test_consolidation_acceptance.py#L38)
- [test_valid_logo_is_canonical_private_png_and_removal_is_audited](../../tests/test_consolidation_acceptance.py#L54)
- [test_commercial_form_cannot_smuggle_fiscal_identity_or_production](../../tests/test_consolidation_acceptance.py#L77)
- [test_company_service_uses_persisted_role_and_rejects_unsupported_currency](../../tests/test_consolidation_acceptance.py#L101)
- [test_hidden_category_cannot_be_added_by_direct_post_or_stale_item](../../tests/test_consolidation_acceptance.py#L114)
- [test_incident_cannot_cross_operational_scope_or_overwrite_concurrent_action](../../tests/test_consolidation_acceptance.py#L129)
- [test_incident_action_history_is_guarded_even_in_raw_sql](../../tests/test_consolidation_acceptance.py#L198)
- [test_http_revocation_invalidates_all_existing_logins_without_changing_credentials](../../tests/test_consolidation_acceptance.py#L225)
- [test_register_and_station_configuration_cannot_invalidate_live_operations](../../tests/test_consolidation_acceptance.py#L250)
- [test_administrative_entity_services_reject_manager_without_http](../../tests/test_consolidation_acceptance.py#L283)
- [test_register_service_checks_terminal_activity_from_database](../../tests/test_consolidation_acceptance.py#L300)
- [test_superadmin_operational_inheritance_does_not_bypass_incident_support_controls](../../tests/test_consolidation_acceptance.py#L313)

## tests/test_consolidation_backend.py

- [test_commercial_settings_partial_save_preserves_fiscal_identity](../../tests/test_consolidation_backend.py#L36)
- [test_invalid_company_settings_rejected_without_mutation](../../tests/test_consolidation_backend.py#L57)
- [test_company_identity_cannot_be_reassigned_after_invoice](../../tests/test_consolidation_backend.py#L65)
- [test_logo_canonical_and_served_only_to_authenticated_user](../../tests/test_consolidation_backend.py#L72)
- [test_commercial_settings_http_and_invalid_section](../../tests/test_consolidation_backend.py#L91)
- [test_category_hiding_blocks_new_line_and_preserves_existing](../../tests/test_consolidation_backend.py#L108)
- [test_station_open_account_blocks_disable_and_reassign](../../tests/test_consolidation_backend.py#L124)
- [test_register_crud_open_session_guard_and_stale_disabled](../../tests/test_consolidation_backend.py#L135)
- [test_register_http_creation_and_edit](../../tests/test_consolidation_backend.py#L155)
- [test_configuration_services_deny_lower_roles](../../tests/test_consolidation_backend.py#L176)
- [test_terminal_preferences_apply_floor_and_cash_selector](../../tests/test_consolidation_backend.py#L188)
- [test_ordering_category_and_station_persists](../../tests/test_consolidation_backend.py#L207)
- [test_filter_ids_extreme_do_not_produce_server_error](../../tests/test_consolidation_backend.py#L229)
- [test_settings_default_get_is_categorized_commercial](../../tests/test_consolidation_backend.py#L234)

## tests/test_consolidation_customer_services.py

- [test_customer_service_mutations_require_role_and_support_pii](../../tests/test_consolidation_customer_services.py#L19)
- [test_edit_staff_name_preserves_credentials_and_requires_current_hierarchy](../../tests/test_consolidation_customer_services.py#L47)

## tests/test_consolidation_documents.py

- [test_receipt_commercial_data_is_frozen_for_pdf_copy_and_refund](../../tests/test_consolidation_documents.py#L18)

## tests/test_consolidation_fiscal.py

- [test_commercial_configuration_changes_do_not_rewrite_fiscal_history](../../tests/test_consolidation_fiscal.py#L27)
- [test_new_authorized_series_applies_only_to_future_documents](../../tests/test_consolidation_fiscal.py#L58)
- [test_refund_keeps_original_identity_when_commercial_settings_change](../../tests/test_consolidation_fiscal.py#L87)
- [test_technical_settings_cannot_replace_external_production_gate](../../tests/test_consolidation_fiscal.py#L102)

## tests/test_consolidation_hardware.py

- [test_output_preferences_persist_and_snapshot_receipt](../../tests/test_consolidation_hardware.py#L29)
- [test_cash_drawer_can_be_disabled_without_removing_receipt](../../tests/test_consolidation_hardware.py#L43)
- [test_test_ticket_obeys_cut_and_explicit_drawer_policy](../../tests/test_consolidation_hardware.py#L52)
- [test_device_configuration_service_denies_lower_roles](../../tests/test_consolidation_hardware.py#L61)
- [test_configurable_output_change_audited_and_inflight_target_protected](../../tests/test_consolidation_hardware.py#L70)
- [test_stale_enabled_printer_cannot_create_or_reroute_work](../../tests/test_consolidation_hardware.py#L88)

## tests/test_consolidation_ops.py

- [test_incident_complete_service_lifecycle_and_retained_history](../../tests/test_consolidation_ops.py#L67)
- [test_incident_stale_form_and_invalid_transition_do_not_add_history](../../tests/test_consolidation_ops.py#L87)
- [test_incident_text_rejects_common_sensitive_payloads](../../tests/test_consolidation_ops.py#L110)
- [test_incident_employee_denied_and_technical_scope_required](../../tests/test_consolidation_ops.py#L115)
- [test_incident_http_creation_classification_resolution_and_search](../../tests/test_consolidation_ops.py#L132)
- [test_incident_sql_history_update_delete_and_replace_blocked](../../tests/test_consolidation_ops.py#L168)
- [test_session_revoke_http_keeps_credentials_and_revokes_existing_login](../../tests/test_consolidation_ops.py#L191)
- [test_terminal_and_user_filters_and_service_authorization](../../tests/test_consolidation_ops.py#L213)
- [test_diagnostics_reports_installed_dependency_versions](../../tests/test_consolidation_ops.py#L228)
- [test_backup_verification_does_not_prepare_maintenance](../../tests/test_consolidation_ops.py#L237)

## tests/test_consolidation_security.py

- [test_explicit_revocation_invalidates_multiple_sessions_without_changing_credentials](../../tests/test_consolidation_security.py#L24)
- [test_service_revocation_denies_insufficient_or_equal_rank](../../tests/test_consolidation_security.py#L48)
- [test_revocation_refreshes_promoted_target_and_demoted_actor](../../tests/test_consolidation_security.py#L58)
- [test_revocation_rejects_disabled_or_revoked_cached_actor](../../tests/test_consolidation_security.py#L70)
- [test_superadmin_revocation_cancels_grants_as_actor_and_approver](../../tests/test_consolidation_security.py#L77)
- [test_superadmin_can_revoke_own_sessions_and_must_authenticate_again](../../tests/test_consolidation_security.py#L94)

## tests/test_fiscal.py

- [test_official_aeat_hash_vectors](../../tests/test_fiscal.py#L11)
- [test_qr_official_url_encoding](../../tests/test_fiscal.py#L45)
- [test_response_never_assumes_acceptance](../../tests/test_fiscal.py#L61)
- [test_soap_schema_identity_and_receipt_persistence](../../tests/test_fiscal.py#L108)
- [test_rejected_correction_flags_and_anulacion_xsd](../../tests/test_fiscal.py#L134)
- [test_invoice_chain_immutable_and_official_xsd](../../tests/test_fiscal.py#L187)
- [test_production_fail_closed](../../tests/test_fiscal.py#L213)
- [test_refund_preserves_original_and_schema](../../tests/test_fiscal.py#L227)
- [test_network_failure_persists_chain](../../tests/test_fiscal.py#L244)
- [test_restore_hold_marker_blocks_remission](../../tests/test_fiscal.py#L259)
- [test_pdf_contains_snapshot_and_test_label](../../tests/test_fiscal.py#L276)
- [test_official_sources_match_pinned_checksums](../../tests/test_fiscal.py#L292)

## tests/test_hardware.py

- [test_receipt_snapshot_qr_cut](../../tests/test_hardware.py#L61)
- [test_original_idempotent_copy_no_drawer](../../tests/test_hardware.py#L74)
- [test_drawer_requires_cash](../../tests/test_hardware.py#L83)
- [test_no_printer_pending](../../tests/test_hardware.py#L88)
- [test_simulator_done_once](../../tests/test_hardware.py#L95)
- [test_production_refuses_simulator](../../tests/test_hardware.py#L105)
- [test_unknown_never_retried](../../tests/test_hardware.py#L112)
- [test_prewrite_failure_retry](../../tests/test_hardware.py#L123)
- [test_expired_lease_unknown](../../tests/test_hardware.py#L132)
- [test_employee_cannot_test_drawer](../../tests/test_hardware.py#L142)
- [test_text_cannot_inject_drawer](../../tests/test_hardware.py#L149)
- [test_job_intent_immutable](../../tests/test_hardware.py#L154)
- [test_tcp_prewrite_failure](../../tests/test_hardware.py#L161)
- [test_tcp_midwrite_unknown](../../tests/test_hardware.py#L168)

## tests/test_regressions.py

- [test_stale_cash_session_cannot_refund_after_closure](../../tests/test_regressions.py#L32)
- [test_sealed_documents_reject_new_lines_and_payments](../../tests/test_regressions.py#L41)
- [test_restore_hold_blocks_services_and_physical_delivery](../../tests/test_regressions.py#L65)
- [test_copies_are_scoped_and_cash_movements_are_append_only](../../tests/test_regressions.py#L79)
- [test_superadmin_panel_renders_real_queue_actions](../../tests/test_regressions.py#L105)
- [test_release_package_contains_versioned_schemas_without_runtime_data](../../tests/test_regressions.py#L119)
- [test_category_management_is_usable_and_protects_assigned_items](../../tests/test_regressions.py#L139)
- [test_customer_export_and_unused_deletion_require_elevated_admin](../../tests/test_regressions.py#L168)

## tests/test_security.py

- [test_role_matrix](../../tests/test_security.py#L28)
- [test_inactive_anonymous_and_unknown_roles_fail](../../tests/test_security.py#L37)
- [test_pin_is_hashed_and_bad_pin_is_rejected](../../tests/test_security.py#L49)
- [test_pin_bruteforce_blocks_across_origins](../../tests/test_security.py#L61)
- [test_admin_cannot_promote_or_edit_peer](../../tests/test_security.py#L72)
- [test_superadmin_can_create_privileged_user_without_default_credentials](../../tests/test_security.py#L84)
- [test_audit_is_append_only_and_metadata_allowlisted](../../tests/test_security.py#L97)
- [test_elevated_session_expires](../../tests/test_security.py#L120)
- [test_createsuperuser_assigns_internal_superadmin](../../tests/test_security.py#L132)
- [test_pin_relogin_clears_previous_elevation](../../tests/test_security.py#L138)
- [test_audit_bulk_upsert_cannot_rewrite_evidence](../../tests/test_security.py#L151)
- [test_audit_preserves_only_valid_evidence_digest](../../tests/test_security.py#L166)
- [test_support_pii_requires_elevation_and_independent_live_approval](../../tests/test_security.py#L174)
- [test_operational_roles_do_not_require_technical_pii_approval](../../tests/test_security.py#L208)
- [test_support_pii_route_coverage](../../tests/test_security.py#L230)
