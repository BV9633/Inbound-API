

fields="""
    STRUCT(
      STRUCT(
        entry_no_1 AS value,
      entry_no_1_confidence_score AS confidence,
  STRUCT(
    entry_no_1_page_number AS page_number,
    [
      STRUCT(entry_no_1_x1_coordinate AS x, entry_no_1_y1_coordinate AS y),
      STRUCT(entry_no_1_x2_coordinate AS x, entry_no_1_y2_coordinate AS y),
      STRUCT(entry_no_1_x3_coordinate AS x, entry_no_1_y3_coordinate AS y),
      STRUCT(entry_no_1_x4_coordinate AS x, entry_no_1_y4_coordinate AS y)
    ] AS normalized_vectors
  ) AS bounding_box
) AS entry_no_1,

      STRUCT(
        entry_no_2 AS value,
        entry_no_2_confidence_score AS confidence,
        STRUCT(
          entry_no_2_page_number AS page_number,
          [
            STRUCT(entry_no_2_x1_coordinate AS x, entry_no_2_y1_coordinate AS y),
            STRUCT(entry_no_2_x2_coordinate AS x, entry_no_2_y2_coordinate AS y),
            STRUCT(entry_no_2_x3_coordinate AS x, entry_no_2_y3_coordinate AS y),
            STRUCT(entry_no_2_x4_coordinate AS x, entry_no_2_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS entry_no_2,

      STRUCT(
        port_code_no AS value,
        port_code_no_confidence_score AS confidence,
        STRUCT(
          port_code_no_page_number AS page_number,
          [
            STRUCT(port_code_no_x1_coordinate AS x, port_code_no_y1_coordinate AS y),
            STRUCT(port_code_no_x2_coordinate AS x, port_code_no_y2_coordinate AS y),
            STRUCT(port_code_no_x3_coordinate AS x, port_code_no_y3_coordinate AS y),
            STRUCT(port_code_no_x4_coordinate AS x, port_code_no_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS port_code_no,

      STRUCT(
        port_of_unlading AS value,
        port_of_unlading_confidence_score AS confidence,
        STRUCT(
          port_of_unlading_page_number AS page_number,
          [
            STRUCT(port_of_unlading_x1_coordinate AS x, port_of_unlading_y1_coordinate AS y),
            STRUCT(port_of_unlading_x2_coordinate AS x, port_of_unlading_y2_coordinate AS y),
            STRUCT(port_of_unlading_x3_coordinate AS x, port_of_unlading_y3_coordinate AS y),
            STRUCT(port_of_unlading_x4_coordinate AS x, port_of_unlading_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS port_of_unlading,

      STRUCT(
        port_of_entry AS value,
        port_of_entry_confidence_score AS confidence,
        STRUCT(
          port_of_entry_page_number AS page_number,
          [
            STRUCT(port_of_entry_x1_coordinate AS x, port_of_entry_y1_coordinate AS y),
            STRUCT(port_of_entry_x2_coordinate AS x, port_of_entry_y2_coordinate AS y),
            STRUCT(port_of_entry_x3_coordinate AS x, port_of_entry_y3_coordinate AS y),
            STRUCT(port_of_entry_x4_coordinate AS x, port_of_entry_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS port_of_entry,

      STRUCT(
        date_of_unlading AS value,
        date_of_unlading_confidence_score AS confidence,
        STRUCT(
          date_of_unlading_page_number AS page_number,
          [
            STRUCT(date_of_unlading_x1_coordinate AS x, date_of_unlading_y1_coordinate AS y),
            STRUCT(date_of_unlading_x2_coordinate AS x, date_of_unlading_y2_coordinate AS y),
            STRUCT(date_of_unlading_x3_coordinate AS x, date_of_unlading_y3_coordinate AS y),
            STRUCT(date_of_unlading_x4_coordinate AS x, date_of_unlading_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS date_of_unlading,

      STRUCT(
        imported_by AS value,
        imported_by_confidence_score AS confidence,
        STRUCT(
          imported_by_page_number AS page_number,
          [
            STRUCT(imported_by_x1_coordinate AS x, imported_by_y1_coordinate AS y),
            STRUCT(imported_by_x2_coordinate AS x, imported_by_y2_coordinate AS y),
            STRUCT(imported_by_x3_coordinate AS x, imported_by_y3_coordinate AS y),
            STRUCT(imported_by_x4_coordinate AS x, imported_by_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS imported_by,

      STRUCT(
        importer_id_IRS AS value,
        importer_id_IRS_confidence_score AS confidence,
        STRUCT(
          importer_id_IRS_page_number AS page_number,
          [
            STRUCT(importer_id_IRS_x1_coordinate AS x, importer_id_IRS_y1_coordinate AS y),
            STRUCT(importer_id_IRS_x2_coordinate AS x, importer_id_IRS_y2_coordinate AS y),
            STRUCT(importer_id_IRS_x3_coordinate AS x, importer_id_IRS_y3_coordinate AS y),
            STRUCT(importer_id_IRS_x4_coordinate AS x, importer_id_IRS_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS importer_id_IRS,

      STRUCT(
        in_bond_via AS value,
        in_bond_via_confidence_score AS confidence,
        STRUCT(
          in_bond_via_page_number AS page_number,
          [
            STRUCT(in_bond_via_x1_coordinate AS x, in_bond_via_y1_coordinate AS y),
            STRUCT(in_bond_via_x2_coordinate AS x, in_bond_via_y2_coordinate AS y),
            STRUCT(in_bond_via_x3_coordinate AS x, in_bond_via_y3_coordinate AS y),
            STRUCT(in_bond_via_x4_coordinate AS x, in_bond_via_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS in_bond_via,

      STRUCT(
        CBP_port_director AS value,
        CBP_port_director_confidence_score AS confidence,
        STRUCT(
          CBP_port_director_page_number AS page_number,
          [
            STRUCT(CBP_port_director_x1_coordinate AS x, CBP_port_director_y1_coordinate AS y),
            STRUCT(CBP_port_director_x2_coordinate AS x, CBP_port_director_y2_coordinate AS y),
            STRUCT(CBP_port_director_x3_coordinate AS x, CBP_port_director_y3_coordinate AS y),
            STRUCT(CBP_port_director_x4_coordinate AS x, CBP_port_director_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS CBP_port_director,

      STRUCT(
        consignee AS value,
        consignee_confidence_score AS confidence,
        STRUCT(
          consignee_page_number AS page_number,
          [
            STRUCT(consignee_x1_coordinate AS x, consignee_y1_coordinate AS y),
            STRUCT(consignee_x2_coordinate AS x, consignee_y2_coordinate AS y),
            STRUCT(consignee_x3_coordinate AS x, consignee_y3_coordinate AS y),
            STRUCT(consignee_x4_coordinate AS x, consignee_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS consignee,

      STRUCT(
        foreign_port_of_lading AS value,
        foreign_port_of_lading_confidence_score AS confidence,
        STRUCT(
          foreign_port_of_lading_page_number AS page_number,
          [
            STRUCT(foreign_port_of_lading_x1_coordinate AS x, foreign_port_of_lading_y1_coordinate AS y),
            STRUCT(foreign_port_of_lading_x2_coordinate AS x, foreign_port_of_lading_y2_coordinate AS y),
            STRUCT(foreign_port_of_lading_x3_coordinate AS x, foreign_port_of_lading_y3_coordinate AS y),
            STRUCT(foreign_port_of_lading_x4_coordinate AS x, foreign_port_of_lading_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS foreign_port_of_lading,

      STRUCT(
        bill_no AS value,
        bill_no_confidence_score AS confidence,
        STRUCT(
          bill_no_page_number AS page_number,
          [
            STRUCT(bill_no_x1_coordinate AS x, bill_no_y1_coordinate AS y),
            STRUCT(bill_no_x2_coordinate AS x, bill_no_y2_coordinate AS y),
            STRUCT(bill_no_x3_coordinate AS x, bill_no_y3_coordinate AS y),
            STRUCT(bill_no_x4_coordinate AS x, bill_no_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS bill_no,

      STRUCT(
        date_of_sailing AS value,
        date_of_sailing_confidence_score AS confidence,
        STRUCT(
          date_of_sailing_page_number AS page_number,
          [
            STRUCT(date_of_sailing_x1_coordinate AS x, date_of_sailing_y1_coordinate AS y),
            STRUCT(date_of_sailing_x2_coordinate AS x, date_of_sailing_y2_coordinate AS y),
            STRUCT(date_of_sailing_x3_coordinate AS x, date_of_sailing_y3_coordinate AS y),
            STRUCT(date_of_sailing_x4_coordinate AS x, date_of_sailing_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS date_of_sailing,

      STRUCT(
        imported_on_vessel_or_carrier AS value,
        imported_on_vessel_or_carrier_confidence_score AS confidence,
        STRUCT(
          imported_on_vessel_or_carrier_page_number AS page_number,
          [
            STRUCT(imported_on_vessel_or_carrier_x1_coordinate AS x, imported_on_vessel_or_carrier_y1_coordinate AS y),
            STRUCT(imported_on_vessel_or_carrier_x2_coordinate AS x, imported_on_vessel_or_carrier_y2_coordinate AS y),
            STRUCT(imported_on_vessel_or_carrier_x3_coordinate AS x, imported_on_vessel_or_carrier_y3_coordinate AS y),
            STRUCT(imported_on_vessel_or_carrier_x4_coordinate AS x, imported_on_vessel_or_carrier_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS imported_on_vessel_or_carrier,

      STRUCT(
        flag AS value,
        flag_confidence_score AS confidence,
        STRUCT(
          flag_page_number AS page_number,
          [
            STRUCT(flag_x1_coordinate AS x, flag_y1_coordinate AS y),
            STRUCT(flag_x2_coordinate AS x, flag_y2_coordinate AS y),
            STRUCT(flag_x3_coordinate AS x, flag_y3_coordinate AS y),
            STRUCT(flag_x4_coordinate AS x, flag_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS flag,

      STRUCT(
        date_imported AS value,
        date_imported_confidence_score AS confidence,
        STRUCT(
          date_imported_page_number AS page_number,
          [
            STRUCT(date_imported_x1_coordinate AS x, date_imported_y1_coordinate AS y),
            STRUCT(date_imported_x2_coordinate AS x, date_imported_y2_coordinate AS y),
            STRUCT(date_imported_x3_coordinate AS x, date_imported_y3_coordinate AS y),
            STRUCT(date_imported_x4_coordinate AS x, date_imported_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS date_imported,

      STRUCT(
        via_last_foreign_port AS value,
        via_last_foreign_port_confidence_score AS confidence,
        STRUCT(
          via_last_foreign_port_page_number AS page_number,
          [
            STRUCT(via_last_foreign_port_x1_coordinate AS x, via_last_foreign_port_y1_coordinate AS y),
            STRUCT(via_last_foreign_port_x2_coordinate AS x, via_last_foreign_port_y2_coordinate AS y),
            STRUCT(via_last_foreign_port_x3_coordinate AS x, via_last_foreign_port_y3_coordinate AS y),
            STRUCT(via_last_foreign_port_x4_coordinate AS x, via_last_foreign_port_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS via_last_foreign_port,

      STRUCT(
        exported_from AS value,
        exported_from_confidence_score AS confidence,
        STRUCT(
          exported_from_page_number AS page_number,
          [
            STRUCT(exported_from_x1_coordinate AS x, exported_from_y1_coordinate AS y),
            STRUCT(exported_from_x2_coordinate AS x, exported_from_y2_coordinate AS y),
            STRUCT(exported_from_x3_coordinate AS x, exported_from_y3_coordinate AS y),
            STRUCT(exported_from_x4_coordinate AS x, exported_from_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS exported_from,

      STRUCT(
        exported_date AS value,
        exported_date_confidence_score AS confidence,
        STRUCT(
          exported_date_page_number AS page_number,
          [
            STRUCT(exported_date_x1_coordinate AS x, exported_date_y1_coordinate AS y),
            STRUCT(exported_date_x2_coordinate AS x, exported_date_y2_coordinate AS y),
            STRUCT(exported_date_x3_coordinate AS x, exported_date_y3_coordinate AS y),
            STRUCT(exported_date_x4_coordinate AS x, exported_date_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS exported_date,

      STRUCT(
        goods_now_at AS value,
        goods_now_at_confidence_score AS confidence,
        STRUCT(
          goods_now_at_page_number AS page_number,
          [
            STRUCT(goods_now_at_x1_coordinate AS x, goods_now_at_y1_coordinate AS y),
            STRUCT(goods_now_at_x2_coordinate AS x, goods_now_at_y2_coordinate AS y),
            STRUCT(goods_now_at_x3_coordinate AS x, goods_now_at_y3_coordinate AS y),
            STRUCT(goods_now_at_x4_coordinate AS x, goods_now_at_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS goods_now_at,

      STRUCT(
        HAWB_number AS value,
        HAWB_number_confidence_score AS confidence,
        STRUCT(
          HAWB_number_page_number AS page_number,
          [
            STRUCT(HAWB_number_x1_coordinate AS x, HAWB_number_y1_coordinate AS y),
            STRUCT(HAWB_number_x2_coordinate AS x, HAWB_number_y2_coordinate AS y),
            STRUCT(HAWB_number_x3_coordinate AS x, HAWB_number_y3_coordinate AS y),
            STRUCT(HAWB_number_x4_coordinate AS x, HAWB_number_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS HAWB_number,

      STRUCT(
        MAWB_number AS value,
        MAWB_number_confidence_score AS confidence,
        STRUCT(
          MAWB_number_page_number AS page_number,
          [
            STRUCT(MAWB_number_x1_coordinate AS x, MAWB_number_y1_coordinate AS y),
            STRUCT(MAWB_number_x2_coordinate AS x, MAWB_number_y2_coordinate AS y),
            STRUCT(MAWB_number_x3_coordinate AS x, MAWB_number_y3_coordinate AS y),
            STRUCT(MAWB_number_x4_coordinate AS x, MAWB_number_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS MAWB_number,

      STRUCT(
        mnfst_quantity AS value,
        mnfst_quantity_confidence_score AS confidence,
        STRUCT(
          mnfst_quantity_page_number AS page_number,
          [
            STRUCT(mnfst_quantity_x1_coordinate AS x, mnfst_quantity_y1_coordinate AS y),
            STRUCT(mnfst_quantity_x2_coordinate AS x, mnfst_quantity_y2_coordinate AS y),
            STRUCT(mnfst_quantity_x3_coordinate AS x, mnfst_quantity_y3_coordinate AS y),
            STRUCT(mnfst_quantity_x4_coordinate AS x, mnfst_quantity_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS mnfst_quantity,

      STRUCT(
        gross_weight AS value,
        gross_weight_confidence_score AS confidence,
        STRUCT(
          gross_weight_page_number AS page_number,
          [
            STRUCT(gross_weight_x1_coordinate AS x, gross_weight_y1_coordinate AS y),
            STRUCT(gross_weight_x2_coordinate AS x, gross_weight_y2_coordinate AS y),
            STRUCT(gross_weight_x3_coordinate AS x, gross_weight_y3_coordinate AS y),
            STRUCT(gross_weight_x4_coordinate AS x, gross_weight_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS gross_weight,

      STRUCT(
        container_number AS value,
        container_number_confidence_score AS confidence,
        STRUCT(
          container_number_page_number AS page_number,
          [
            STRUCT(container_number_x1_coordinate AS x, container_number_y1_coordinate AS y),
            STRUCT(container_number_x2_coordinate AS x, container_number_y2_coordinate AS y),
            STRUCT(container_number_x3_coordinate AS x, container_number_y3_coordinate AS y),
            STRUCT(container_number_x4_coordinate AS x, container_number_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS container_number,

      STRUCT(
        seal_number AS value,
        seal_number_confidence_score AS confidence,
        STRUCT(
          seal_number_page_number AS page_number,
          [
            STRUCT(seal_number_x1_coordinate AS x, seal_number_y1_coordinate AS y),
            STRUCT(seal_number_x2_coordinate AS x, seal_number_y2_coordinate AS y),
            STRUCT(seal_number_x3_coordinate AS x, seal_number_y3_coordinate AS y),
            STRUCT(seal_number_x4_coordinate AS x, seal_number_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS seal_number,

      STRUCT(
        SLAC AS value,
        SLAC_confidence_score AS confidence,
        STRUCT(
          SLAC_page_number AS page_number,
          [
            STRUCT(SLAC_x1_coordinate AS x, SLAC_y1_coordinate AS y),
            STRUCT(SLAC_x2_coordinate AS x, SLAC_y2_coordinate AS y),
            STRUCT(SLAC_x3_coordinate AS x, SLAC_y3_coordinate AS y),
            STRUCT(SLAC_x4_coordinate AS x, SLAC_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS SLAC,
      
      STRUCT(
        Value_in_dollars AS value,
        Value_in_dollars_confidence_score AS confidence,
        STRUCT(
          Value_in_dollars_page_number AS page_number,
          [
            STRUCT(Value_in_dollars_x1_coordinate AS x, Value_in_dollars_y1_coordinate AS y),
            STRUCT(Value_in_dollars_x2_coordinate AS x, Value_in_dollars_y2_coordinate AS y),
            STRUCT(Value_in_dollars_x3_coordinate AS x, Value_in_dollars_y3_coordinate AS y),
            STRUCT(Value_in_dollars_x4_coordinate AS x, Value_in_dollars_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS Value_in_dollars,
      
      reviewed_by AS reviewed_by,
      review_date AS review_date,
      created_by AS created_by,
      original_creation_date AS original_creation_date,
      last_updated_date AS last_updated_date,
      reason_or_remarks AS reason_or_remarks,
      minimum_confidence AS minimum_confidence,
      status AS status
    ) AS header_fields,

    """