

fields="""
    STRUCT(
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
        country_of_export AS value,
        country_of_export_confidence_score AS confidence,
        STRUCT(
          country_of_export_page_number AS page_number,
          [
            STRUCT(country_of_export_x1_coordinate AS x, country_of_export_y1_coordinate AS y),
            STRUCT(country_of_export_x2_coordinate AS x, country_of_export_y2_coordinate AS y),
            STRUCT(country_of_export_x3_coordinate AS x, country_of_export_y3_coordinate AS y),
            STRUCT(country_of_export_x4_coordinate AS x, country_of_export_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS country_of_export,

      STRUCT(
        ASN_number AS value,
        ASN_number_confidence_score AS confidence,
        STRUCT(
          ASN_number_page_number AS page_number,
          [
            STRUCT(ASN_number_x1_coordinate AS x, ASN_number_y1_coordinate AS y),
            STRUCT(ASN_number_x2_coordinate AS x, ASN_number_y2_coordinate AS y),
            STRUCT(ASN_number_x3_coordinate AS x, ASN_number_y3_coordinate AS y),
            STRUCT(ASN_number_x4_coordinate AS x, ASN_number_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS ASN_number,

        STRUCT(
        flight_data AS value,
        flight_data_confidence_score AS confidence,
        STRUCT(
          flight_data_page_number AS page_number,
          [
            STRUCT(flight_data_x1_coordinate AS x, flight_data_y1_coordinate AS y),
            STRUCT(flight_data_x2_coordinate AS x, flight_data_y2_coordinate AS y),
            STRUCT(flight_data_x3_coordinate AS x, flight_data_y3_coordinate AS y),
            STRUCT(flight_data_x4_coordinate AS x, flight_data_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS flight_data,

        STRUCT(
        airport_of_departure AS value,
        airport_of_departure_confidence_score AS confidence,
        STRUCT(
          airport_of_departure_page_number AS page_number,
          [
            STRUCT(airport_of_departure_x1_coordinate AS x, airport_of_departure_y1_coordinate AS y),
            STRUCT(airport_of_departure_x2_coordinate AS x, airport_of_departure_y2_coordinate AS y),
            STRUCT(airport_of_departure_x3_coordinate AS x, airport_of_departure_y3_coordinate AS y),
            STRUCT(airport_of_departure_x4_coordinate AS x, airport_of_departure_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS airport_of_departure,

      -- airport_of_destination
      STRUCT(
        airport_of_destination AS value,
        airport_of_destination_confidence_score AS confidence,
        STRUCT(
          airport_of_destination_page_number AS page_number,
          [
            STRUCT(airport_of_destination_x1_coordinate AS x, airport_of_destination_y1_coordinate AS y),
            STRUCT(airport_of_destination_x2_coordinate AS x, airport_of_destination_y2_coordinate AS y),
            STRUCT(airport_of_destination_x3_coordinate AS x, airport_of_destination_y3_coordinate AS y),
            STRUCT(airport_of_destination_x4_coordinate AS x, airport_of_destination_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS airport_of_destination,

        STRUCT(
        port_of_loading AS value,
        port_of_loading_confidence_score AS confidence,
        STRUCT(
          port_of_loading_page_number AS page_number,
          [
            STRUCT(port_of_loading_x1_coordinate AS x, port_of_loading_y1_coordinate AS y),
            STRUCT(port_of_loading_x2_coordinate AS x, port_of_loading_y2_coordinate AS y),
            STRUCT(port_of_loading_x3_coordinate AS x, port_of_loading_y3_coordinate AS y),
            STRUCT(port_of_loading_x4_coordinate AS x, port_of_loading_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS port_of_loading,

      STRUCT(
        port_of_discharge AS value,
        port_of_discharge_confidence_score AS confidence,
        STRUCT(
          port_of_discharge_page_number AS page_number,
          [
            STRUCT(port_of_discharge_x1_coordinate AS x, port_of_discharge_y1_coordinate AS y),
            STRUCT(port_of_discharge_x2_coordinate AS x, port_of_discharge_y2_coordinate AS y),
            STRUCT(port_of_discharge_x3_coordinate AS x, port_of_discharge_y3_coordinate AS y),
            STRUCT(port_of_discharge_x4_coordinate AS x, port_of_discharge_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS port_of_discharge,

      STRUCT(
        transportation_mode AS value,
        transportation_mode_confidence_score AS confidence,
        STRUCT(
          transportation_mode_page_number AS page_number,
          [
            STRUCT(transportation_mode_x1_coordinate AS x, transportation_mode_y1_coordinate AS y),
            STRUCT(transportation_mode_x2_coordinate AS x, transportation_mode_y2_coordinate AS y),
            STRUCT(transportation_mode_x3_coordinate AS x, transportation_mode_y3_coordinate AS y),
            STRUCT(transportation_mode_x4_coordinate AS x, transportation_mode_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS transportation_mode,

      -- shippers_name_and_address
      STRUCT(
        shippers_name_and_address AS value,
        shippers_name_and_address_confidence_score AS confidence,
        STRUCT(
          shippers_name_and_address_page_number AS page_number,
          [
            STRUCT(shippers_name_and_address_x1_coordinate AS x, shippers_name_and_address_y1_coordinate AS y),
            STRUCT(shippers_name_and_address_x2_coordinate AS x, shippers_name_and_address_y2_coordinate AS y),
            STRUCT(shippers_name_and_address_x3_coordinate AS x, shippers_name_and_address_y3_coordinate AS y),
            STRUCT(shippers_name_and_address_x4_coordinate AS x, shippers_name_and_address_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS shippers_name_and_address,

      -- MAWB_number
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

      -- vessel_or_voyage
      STRUCT(
        vessel_or_voyage AS value,
        vessel_or_voyage_confidence_score AS confidence,
        STRUCT(
          vessel_or_voyage_page_number AS page_number,
          [
            STRUCT(vessel_or_voyage_x1_coordinate AS x, vessel_or_voyage_y1_coordinate AS y),
            STRUCT(vessel_or_voyage_x2_coordinate AS x, vessel_or_voyage_y2_coordinate AS y),
            STRUCT(vessel_or_voyage_x3_coordinate AS x, vessel_or_voyage_y3_coordinate AS y),
            STRUCT(vessel_or_voyage_x4_coordinate AS x, vessel_or_voyage_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS vessel_or_voyage,

      -- total_quantity
      STRUCT(
        total_quantity AS value,
        total_quantity_confidence_score AS confidence,
        STRUCT(
          total_quantity_page_number AS page_number,
          [
            STRUCT(total_quantity_x1_coordinate AS x, total_quantity_y1_coordinate AS y),
            STRUCT(total_quantity_x2_coordinate AS x, total_quantity_y2_coordinate AS y),
            STRUCT(total_quantity_x3_coordinate AS x, total_quantity_y3_coordinate AS y),
            STRUCT(total_quantity_x4_coordinate AS x, total_quantity_y4_coordinate AS y)
          ] AS normalized_vectors
        ) AS bounding_box
      ) AS total_quantity,

      reviewed_by AS reviewed_by,
      review_date AS review_date,
      created_by AS created_by,
      original_creation_date AS original_creation_date,
      last_updated_date AS last_updated_date,
      reason_or_remarks AS reason_or_remarks,
      minimum_confidence AS minimum_confidence,
      status AS status
    ) AS header_fields,

    -- ===========================
    -- LINE ITEMS (array)
    -- ===========================
    ARRAY(
      SELECT AS STRUCT
        li.line_item_id AS line_item_id,
        STRUCT(
          -- container_number
          STRUCT(
            li.container_number AS value,
            li.container_number_confidence_score AS confidence,
            STRUCT(
              li.container_number_page_number AS page_number,
              [
                STRUCT(li.container_number_x1_coordinate AS x, li.container_number_y1_coordinate AS y),
                STRUCT(li.container_number_x2_coordinate AS x, li.container_number_y2_coordinate AS y),
                STRUCT(li.container_number_x3_coordinate AS x, li.container_number_y3_coordinate AS y),
                STRUCT(li.container_number_x4_coordinate AS x, li.container_number_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS container_number,

          -- seal_number
          STRUCT(
            li.seal_number AS value,
            li.seal_number_confidence_score AS confidence,
            STRUCT(
              li.seal_number_page_number AS page_number,
              [
                STRUCT(li.seal_number_x1_coordinate AS x, li.seal_number_y1_coordinate AS y),
                STRUCT(li.seal_number_x2_coordinate AS x, li.seal_number_y2_coordinate AS y),
                STRUCT(li.seal_number_x3_coordinate AS x, li.seal_number_y3_coordinate AS y),
                STRUCT(li.seal_number_x4_coordinate AS x, li.seal_number_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS seal_number,

          -- PO_number
          STRUCT(
            li.PO_number AS value,
            li.PO_number_confidence_score AS confidence,
            STRUCT(
              li.PO_number_page_number AS page_number,
              [
                STRUCT(li.PO_number_x1_coordinate AS x, li.PO_number_y1_coordinate AS y),
                STRUCT(li.PO_number_x2_coordinate AS x, li.PO_number_y2_coordinate AS y),
                STRUCT(li.PO_number_x3_coordinate AS x, li.PO_number_y3_coordinate AS y),
                STRUCT(li.PO_number_x4_coordinate AS x, li.PO_number_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS PO_number,

          -- mnfst_qty
          STRUCT(
            li.mnfst_qty AS value,
            li.mnfst_qty_confidence_score AS confidence,
            STRUCT(
              li.mnfst_qty_page_number AS page_number,
              [
                STRUCT(li.mnfst_qty_x1_coordinate AS x, li.mnfst_qty_y1_coordinate AS y),
                STRUCT(li.mnfst_qty_x2_coordinate AS x, li.mnfst_qty_y2_coordinate AS y),
                STRUCT(li.mnfst_qty_x3_coordinate AS x, li.mnfst_qty_y3_coordinate AS y),
                STRUCT(li.mnfst_qty_x4_coordinate AS x, li.mnfst_qty_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS mnfst_qty,

          -- SLAC
          STRUCT(
            li.SLAC AS value,
            li.SLAC_confidence_score AS confidence,
            STRUCT(
              li.SLAC_page_number AS page_number,
              [
                STRUCT(li.SLAC_x1_coordinate AS x, li.SLAC_y1_coordinate AS y),
                STRUCT(li.SLAC_x2_coordinate AS x, li.SLAC_y2_coordinate AS y),
                STRUCT(li.SLAC_x3_coordinate AS x, li.SLAC_y3_coordinate AS y),
                STRUCT(li.SLAC_x4_coordinate AS x, li.SLAC_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS SLAC,

          -- gross_weight
          STRUCT(
            li.gross_weight AS value,
            li.gross_weight_confidence_score AS confidence,
            STRUCT(
              li.gross_weight_page_number AS page_number,
              [
                STRUCT(li.gross_weight_x1_coordinate AS x, li.gross_weight_y1_coordinate AS y),
                STRUCT(li.gross_weight_x2_coordinate AS x, li.gross_weight_y2_coordinate AS y),
                STRUCT(li.gross_weight_x3_coordinate AS x, li.gross_weight_y3_coordinate AS y),
                STRUCT(li.gross_weight_x4_coordinate AS x, li.gross_weight_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS gross_weight,

          -- chargable_weight
          STRUCT(
            li.chargable_weight AS value,
            li.chargable_weight_confidence_score AS confidence,
            STRUCT(
              li.chargable_weight_page_number AS page_number,
              [
                STRUCT(li.chargable_weight_x1_coordinate AS x, li.chargable_weight_y1_coordinate AS y),
                STRUCT(li.chargable_weight_x2_coordinate AS x, li.chargable_weight_y2_coordinate AS y),
                STRUCT(li.chargable_weight_x3_coordinate AS x, li.chargable_weight_y3_coordinate AS y),
                STRUCT(li.chargable_weight_x4_coordinate AS x, li.chargable_weight_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS chargable_weight,

          -- volume
          STRUCT(
            li.volume AS value,
            li.volume_confidence_score AS confidence,
            STRUCT(
              li.volume_page_number AS page_number,
              [
                STRUCT(li.volume_x1_coordinate AS x, li.volume_y1_coordinate AS y),
                STRUCT(li.volume_x2_coordinate AS x, li.volume_y2_coordinate AS y),
                STRUCT(li.volume_x3_coordinate AS x, li.volume_y3_coordinate AS y),
                STRUCT(li.volume_x4_coordinate AS x, li.volume_y4_coordinate AS y)
              ] AS normalized_vectors
            ) AS bounding_box
          ) AS volume
        ) AS header_fields
      FROM UNNEST(line_items) AS li
    ) AS line_items
"""