from flask import Blueprint, request, jsonify
from data_processing import preprocess_and_cluster

cluster_bp = Blueprint('cluster_bp', __name__)

@cluster_bp.route('/cluster', methods=['POST'])
def cluster():
    try:
        access_logs = request.json
        clustered = preprocess_and_cluster(access_logs)
        return jsonify(clustered), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
