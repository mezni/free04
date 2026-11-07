use redis::{Client, aio::MultiplexedConnection};
use std::error::Error;

/// Redis connection pool client
pub struct RedisClient {
    connection: MultiplexedConnection,
}

impl RedisClient {
    /// Create a new Redis client connection
    pub async fn new(redis_url: &str) -> Result<Self, redis::RedisError> {
        let client = Client::open(redis_url)?;
        let mut con = client.get_async_connection().await?;
        Ok(Self { connection: con })
    }

    /// Check if a spec ID has been seen (SISMEMBER)
    pub async fn is_duplicate(&mut self, spec_id: &str) -> Result<bool, redis::RedisError> {
        let result: redis::CmdFnIntegeR<_, _> = redis::cmd("SISMEMBER")
            .arg("active_spec_ids")
            .arg(spec_id)
            .query_async(&mut self.connection)
            .await?;
        Ok(result == 1)
    }

    /// Add a spec ID to the tracked set (SADD)
    pub async fn mark_seen(&mut self, spec_id: &str) -> Result<usize, redis::RedisError> {
        let result: redis::CmdFnIntegeR<_, _> = redis::cmd("SADD")
            .arg("active_spec_ids")
            .arg(spec_id)
            .query_async(&mut self.connection)
            .await?;
        Ok(result)
    }

    /// Set TTL on the active_spec_ids set (EXPIRE)
    pub async fn set_ttl(&mut self, seconds: u64) -> Result<bool, redis::RedisError> {
        let result: redis::CmdFnBoolean<_> = redis::cmd("EXPIRE")
            .arg("active_spec_ids")
            .arg(seconds)
            .query_async(&mut self.connection)
            .await?;
        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_redis_client_creation() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let client = rt.block_on(async {
            RedisClient::new("redis://localhost:6379").await
        });
        assert!(client.is_ok());
    }
}