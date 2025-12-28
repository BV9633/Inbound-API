from pydantic import BaseModel,Field
from typing import Optional,List

fields="""
    STRUCT(
        STRUCT(
            invoice_number AS value,
            invoice_number_confidence_score AS confidence,
            STRUCT (
                invoice_number_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(invoice_number_x1_cordinate AS x, invoice_number_y1_cordinate AS y),
                STRUCT(invoice_number_x2_cordinate AS x, invoice_number_y2_cordinate AS y),
                STRUCT(invoice_number_x3_cordinate AS x, invoice_number_y3_cordinate AS y),
                STRUCT(invoice_number_x4_cordinate AS x, invoice_number_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS invoice_number,   

        STRUCT(
            Incoterm AS value,
            Incoterm_confidence_score AS confidence,
            STRUCT (
                Incoterm_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(Incoterm_x1_cordinate AS x, Incoterm_y1_cordinate AS y),
                STRUCT(Incoterm_x2_cordinate AS x, Incoterm_y2_cordinate AS y),
                STRUCT(Incoterm_x3_cordinate AS x, Incoterm_y3_cordinate AS y),
                STRUCT(Incoterm_x4_cordinate AS x, Incoterm_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS Incoterm,

        STRUCT(
            commercial_invoice_value AS value,
            commercial_invoice_value_confidence_score AS confidence,
            STRUCT (
                commercial_invoice_value_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(commercial_invoice_value_x1_cordinate AS x, commercial_invoice_value_y1_cordinate AS y),
                STRUCT(commercial_invoice_value_x2_cordinate AS x, commercial_invoice_value_y2_cordinate AS y),
                STRUCT(commercial_invoice_value_x3_cordinate AS x, commercial_invoice_value_y3_cordinate AS y),
                STRUCT(commercial_invoice_value_x4_cordinate AS x, commercial_invoice_value_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS commercial_invoice_value,

        STRUCT(
            supplier_name AS value,
            supplier_name_confidence_score AS confidence,
            STRUCT (
                supplier_name_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(supplier_name_x1_cordinate AS x, supplier_name_y1_cordinate AS y),
                STRUCT(supplier_name_x2_cordinate AS x, supplier_name_y2_cordinate AS y),
                STRUCT(supplier_name_x3_cordinate AS x, supplier_name_y3_cordinate AS y),
                STRUCT(supplier_name_x4_cordinate AS x, supplier_name_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS supplier_name,

        STRUCT(
            supplier_location AS value,
            supplier_location_confidence_score AS confidence,
            STRUCT (
                supplier_location_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(supplier_location_x1_cordinate AS x, supplier_location_y1_cordinate AS y),
                STRUCT(supplier_location_x2_cordinate AS x, supplier_location_y2_cordinate AS y),
                STRUCT(supplier_location_x3_cordinate AS x, supplier_location_y3_cordinate AS y),
                STRUCT(supplier_location_x4_cordinate AS x, supplier_location_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS supplier_location,

        STRUCT(
            HAWB_number AS value,
            HAWB_number_confidence_score AS confidence,
            STRUCT (
                HAWB_number_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(HAWB_number_x1_cordinate AS x, HAWB_number_y1_cordinate AS y),
                STRUCT(HAWB_number_x2_cordinate AS x, HAWB_number_y2_cordinate AS y),
                STRUCT(HAWB_number_x3_cordinate AS x, HAWB_number_y3_cordinate AS y),
                STRUCT(HAWB_number_x4_cordinate AS x, HAWB_number_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS HAWB_number,

        STRUCT(
            MAWB_number AS value,
            MAWB_number_confidence_score AS confidence,
            STRUCT (
                MAWB_number_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(MAWB_number_x1_cordinate AS x, MAWB_number_y1_cordinate AS y),
                STRUCT(MAWB_number_x2_cordinate AS x, MAWB_number_y2_cordinate AS y),
                STRUCT(MAWB_number_x3_cordinate AS x, MAWB_number_y3_cordinate AS y),
                STRUCT(MAWB_number_x4_cordinate AS x, MAWB_number_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS MAWB_number,

        
        STRUCT(
            currency AS value,
            currency_confidence_score AS confidence,
            STRUCT (
                currency_page_number as page_number,
                ARRAY<
                STRUCT<x FLOAT64, y FLOAT64>
                >[
                STRUCT(currency_x1_cordinate AS x, currency_y1_cordinate AS y),
                STRUCT(currency_x2_cordinate AS x, currency_y2_cordinate AS y),
                STRUCT(currency_x3_cordinate AS x, currency_y3_cordinate AS y),
                STRUCT(currency_x4_cordinate AS x, currency_y4_cordinate AS y)
                ] AS normalized_vectors
            ) AS bounding_box
        ) AS currency,

        reviewed_by,review_date,created_by,original_creation_date,last_updated_date,
        reason_or_remarks,minimum_confidence,status
    ) AS header_fields,
    ARRAY(
            SELECT STRUCT(
            li.line_item_id AS line_item_id,
            STRUCT(
                STRUCT(
                    li.part_number AS value,
                    li.part_number_confidence_score AS confidence,
                    STRUCT (
                    li.part_number_page_number as page_number,
                    ARRAY<
                    STRUCT<x FLOAT64, y FLOAT64>
                    >[
                    STRUCT(li.part_number_x1_cordinate AS x, li.part_number_y1_cordinate AS y),
                    STRUCT(li.part_number_x2_cordinate AS x, li.part_number_y2_cordinate AS y),
                    STRUCT(li.part_number_x3_cordinate AS x, li.part_number_y3_cordinate AS y),
                    STRUCT(li.part_number_x4_cordinate AS x, li.part_number_y4_cordinate AS y)
                    ] AS normalized_vectors
                    ) AS bounding_box
                ) AS part_number,

                STRUCT(
                    li.unit_price AS value,
                    li.unit_price_confidence_score AS confidence,
                    STRUCT (
                    li.unit_price_page_number as page_number,
                    ARRAY<
                    STRUCT<x FLOAT64, y FLOAT64>
                    >[
                    STRUCT(li.unit_price_x1_cordinate AS x, li.unit_price_y1_cordinate AS y),
                    STRUCT(li.unit_price_x2_cordinate AS x, li.unit_price_y2_cordinate AS y),
                    STRUCT(li.unit_price_x3_cordinate AS x, li.unit_price_y3_cordinate AS y),
                    STRUCT(li.unit_price_x4_cordinate AS x, li.unit_price_y4_cordinate AS y)
                    ] AS normalized_vectors
                    ) AS bounding_box
                ) AS unit_price,

                STRUCT(
                    li.Total_Value AS value,
                    li.Total_Value_confidence_score AS confidence,
                    STRUCT (
                    li.Total_Value_page_number as page_number,
                    ARRAY<
                    STRUCT<x FLOAT64, y FLOAT64>
                    >[
                    STRUCT(li.Total_Value_x1_cordinate AS x, li.Total_Value_y1_cordinate AS y),
                    STRUCT(li.Total_Value_x2_cordinate AS x, li.Total_Value_y2_cordinate AS y),
                    STRUCT(li.Total_Value_x3_cordinate AS x, li.Total_Value_y3_cordinate AS y),
                    STRUCT(li.Total_Value_x4_cordinate AS x, li.Total_Value_y4_cordinate AS y)
                    ] AS normalized_vectors
                    ) AS bounding_box
                ) AS Total_Value,

                STRUCT(
                    li.Quantity AS value,
                    li.Quantity_confidence_score AS confidence,
                    STRUCT (
                    li.Quantity_page_number as page_number,
                    ARRAY<
                    STRUCT<x FLOAT64, y FLOAT64>
                    >[
                    STRUCT(li.Quantity_x1_cordinate AS x, li.Quantity_y1_cordinate AS y),
                    STRUCT(li.Quantity_x2_cordinate AS x, li.Quantity_y2_cordinate AS y),
                    STRUCT(li.Quantity_x3_cordinate AS x, li.Quantity_y3_cordinate AS y),
                    STRUCT(li.Quantity_x4_cordinate AS x, li.Quantity_y4_cordinate AS y)
                    ] AS normalized_vectors
                    ) AS bounding_box
                ) AS Quantity,

                STRUCT(
                    li.country_of_origin AS value,
                    li.country_of_origin_confidence_score AS confidence,
                    STRUCT (
                    li.country_of_origin_page_number as page_number,
                    ARRAY<
                    STRUCT<x FLOAT64, y FLOAT64>
                    >[
                    STRUCT(li.country_of_origin_x1_cordinate AS x, li.country_of_origin_y1_cordinate AS y),
                    STRUCT(li.country_of_origin_x2_cordinate AS x, li.country_of_origin_y2_cordinate AS y),
                    STRUCT(li.country_of_origin_x3_cordinate AS x, li.country_of_origin_y3_cordinate AS y),
                    STRUCT(li.country_of_origin_x4_cordinate AS x, li.country_of_origin_y4_cordinate AS y)
                    ] AS normalized_vectors
                    ) AS bounding_box
                ) AS country_of_origin,

                STRUCT(
                    li.PO AS value,
                    li.PO_confidence_score AS confidence,
                    STRUCT (
                    li.PO_page_number as page_number,
                    ARRAY<
                    STRUCT<x FLOAT64, y FLOAT64>
                    >[
                    STRUCT(li.PO_x1_cordinate AS x, li.PO_y1_cordinate AS y),
                    STRUCT(li.PO_x2_cordinate AS x, li.PO_y2_cordinate AS y),
                    STRUCT(li.PO_x3_cordinate AS x, li.PO_y3_cordinate AS y),
                    STRUCT(li.PO_x4_cordinate AS x, li.PO_y4_cordinate AS y)
                    ] AS normalized_vectors
                    ) AS bounding_box
                ) AS PO,

                STRUCT(
                    li.ASN AS value,
                    li.ASN_confidence_score AS confidence,
                    STRUCT (
                    li.ASN_page_number as page_number,
                    ARRAY<
                    STRUCT<x FLOAT64, y FLOAT64>
                    >[
                    STRUCT(li.ASN_x1_cordinate AS x, li.ASN_y1_cordinate AS y),
                    STRUCT(li.ASN_x2_cordinate AS x, li.ASN_y2_cordinate AS y),
                    STRUCT(li.ASN_x3_cordinate AS x, li.ASN_y3_cordinate AS y),
                    STRUCT(li.ASN_x4_cordinate AS x, li.ASN_y4_cordinate AS y)
                    ] AS normalized_vectors
                    ) AS bounding_box
                ) AS ASN
                ) AS header_fields
            )
            FROM UNNEST(line_items) AS li
        ) AS line_items,

    """
class Normalized_vectors(BaseModel):
    x:Optional[float]=Field(default=None)
    y:Optional[float]=Field(default=None)

class Bounding_box(BaseModel):
    page_number:Optional[int]=Field(default=None)
    normalized_vectors:List[Normalized_vectors]

class Item(BaseModel):
    value:Optional[str]=Field(default=None)
    confidence:Optional[float]=Field(default=None)
    bounding_box:Bounding_box

class Header_fields(BaseModel):
    invoice_number:Item
    Incoterm:Item
    commercial_invoice_value:Item
    supplier_name:Item
    supplier_location:Item
    HAWB_number:Item
    MAWB_number:Item
    currency:Item
    reviewed_by:Optional[str]=Field(default=None)
    review_date:Optional[str]=Field(default=None)
    created_by:Optional[str]=Field(default=None)
    original_creation_date:Optional[str]=Field(default=None)
    last_updated_date:Optional[str]=Field(default=None)
    reason_or_remarks:Optional[str]=Field(default=None)
    minimum_confidence:Optional[float]=Field(default=None)
    status:Optional[str]=Field(default=None)

class Line_items_header_fields(BaseModel):
    part_number:Item
    unit_price:Item
    Total_Value:Item
    Quantity:Item
    country_of_origin:Item
    PO:Item
    ASN:Item

class Line_items(BaseModel):
    line_item_id:str
    header_fields:Line_items_header_fields

class Evaluation_data(BaseModel):
    header_fields:Header_fields
    line_items:List[Line_items]

class Invoice(BaseModel):
    invoice_id:str
    original_document_url:Optional[str]=Field(default=None)
    evaluation_data:Evaluation_data