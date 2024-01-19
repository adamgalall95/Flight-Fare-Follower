import pandas as pd
from pathlib import Path
from sqlalchemy import Table, MetaData
from etl.connectors.postgresql import PostgreSqlClient
from etl.connectors.exchange_api import ExchangeApiClient
from datetime import datetime, timedelta


def extract_load_airport_currencies(
    exchange_api_client: ExchangeApiClient,
    postgresql_client: PostgreSqlClient,
    airport_currency_reference_path: Path,
    table: Table,
    metadata: MetaData,
) -> pd.DataFrame:
    """
    This function extracts and loads currency exchange using an Exchange API client and a PostgreSQL client.
    It reads a list of airport codes and their corresponding currencies from a CSV file, fetches the
    latest exchange rates using the Exchange API, and then merges this data with the airport information.
    The merged data is then upserted into a specified PostgreSQL database table.

    Parameters:
        exchange_api_client (ExchangeApiClient): An instance of ExchangeApiClient to fetch exchange rate data.
        postgresql_client (PostgreSqlClient): An instance of PostgreSqlClient for database operations.
        airport_currency_reference_path (Path): The file path to the CSV containing airport and currency data.
        table (Table): The SQLAlchemy table object where data will be upserted.
        metadata (MetaData): The SQLAlchemy MetaData object associated with the database.

    Returns:
        pd.DataFrame: A DataFrame containing the combined data of airport currencies and their latest exchange rates.
    """
    df_airport_currencies = pd.read_csv(airport_currency_reference_path)
    current_date = datetime.now()
    current_date_formatted = current_date.strftime("%Y-%m-%d")
    exchange_currency_data = exchange_api_client.get_exchange_rates()
    df_combined = pd.merge(
        df_airport_currencies, exchange_currency_data, on="currencyCode"
    )
    df_combined["viewedAt"] = current_date_formatted
    df_combined = df_combined[["viewedAt", "currencyCode", "airportCode", "value"]]
    postgresql_client.upsert(
        data=df_combined.to_dict(orient="records"), table=table, metadata=metadata
    )
    return df_combined
