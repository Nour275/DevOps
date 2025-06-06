import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.cluster import KMeans

def preprocess_and_cluster(data):
    df = pd.DataFrame(data)

    # Encode IP, resource, and status
    le_ip = LabelEncoder()
    le_resource = LabelEncoder()
    le_status = LabelEncoder()

    df['ip_encoded'] = le_ip.fit_transform(df['source_ip'])
    df['resource_encoded'] = le_resource.fit_transform(df['resource_accessed'])
    df['status_encoded'] = le_status.fit_transform(df['status'])

    # Select features for clustering
    X = df[['ip_encoded', 'user_id', 'resource_encoded', 'status_encoded']]

    # Apply KMeans
    kmeans = KMeans(n_clusters=2, random_state=0)
    df['cluster'] = kmeans.fit_predict(X)

    return df.to_dict(orient='records')
