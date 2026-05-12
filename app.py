from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from backend.algorithms import analyze_scenario
from backend.sample_data import build_sample_scenario

app = Flask(__name__, static_folder="static", template_folder="templates")
BASE_SCENARIO = build_sample_scenario()
DB_PATH = Path(__file__).with_name("scenario.sqlite3")


def _open_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _init_db() -> None:
    with _open_db() as connection:
      connection.execute(
          """
          CREATE TABLE IF NOT EXISTS scenario_state (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              payload TEXT NOT NULL
          )
          """
      )
      row = connection.execute("SELECT 1 FROM scenario_state WHERE id = 1").fetchone()
      if row is None:
          connection.execute(
              "INSERT INTO scenario_state (id, payload) VALUES (1, ?)",
              (json.dumps(BASE_SCENARIO),),
          )


def _load_scenario() -> dict:
    with _open_db() as connection:
        row = connection.execute("SELECT payload FROM scenario_state WHERE id = 1").fetchone()
        if row is None:
            return deepcopy(BASE_SCENARIO)
        return json.loads(row["payload"])


def _save_scenario(scenario: dict) -> dict:
    with _open_db() as connection:
        connection.execute(
            "INSERT INTO scenario_state (id, payload) VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
            (json.dumps(scenario),),
        )
    return scenario


_init_db()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/scenario")
def scenario():
    return jsonify(_load_scenario())


@app.post("/api/scenario")
def save_scenario():
    payload = request.get_json(silent=True) or {}
    scenario_data = payload.get("scenario")
    if scenario_data is None:
        return jsonify(_load_scenario())
    return jsonify(_save_scenario(scenario_data))


@app.post("/api/scenario/reset")
def reset_scenario():
    return jsonify(_save_scenario(deepcopy(BASE_SCENARIO)))


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    scenario_data = payload.get("scenario") or _load_scenario()
    result = analyze_scenario(
        scenario_data,
        batch_size=payload.get("batchSize"),
        weight_capacity=payload.get("weightCapacity"),
        volume_capacity=payload.get("volumeCapacity"),
    )
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
