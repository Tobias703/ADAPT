use anyhow::Result;
use clap::Parser;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tracing::{info, warn, error};

/// Minimal PT server: accepts obfuscated connections and proxies them to a backend (Tor ORPort).
#[derive(Parser, Debug)]
#[command(author, version, about)]
struct Opt {
    /// Listen address for obfuscated transports (e.g. 0.0.0.0:443)
    #[arg(long, default_value = "127.0.0.1:1984")]
    listen: String,

    /// Backend Tor bridge address (ORPort) or local Tor instance (e.g. 127.0.0.1:9001)
    #[arg(long, default_value = "127.0.0.1:9001")]
    backend: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    // init logging (respect RUST_LOG env var)
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let opt = Opt::parse();

    let listener = TcpListener::bind(&opt.listen).await?;
    info!("pt-server listening on {}", opt.listen);
    info!("proxying connections to backend {}", opt.backend);

    loop {
        match listener.accept().await {
            Ok((socket, peer)) => {
                let backend = opt.backend.clone();
                info!("accepted connection from {}", peer);
                tokio::spawn(async move {
                    if let Err(e) = handle_conn(socket, &backend).await {
                        warn!("connection handler error from {}: {:?}", peer, e);
                    }
                });
            }
            Err(e) => {
                error!("accept error: {:?}", e);
            }
        }
    }
}

/// Per-connection handler: perform optional server-side handshake/transform and proxy to backend
async fn handle_conn(mut inbound: TcpStream, backend_addr: &str) -> Result<()> {
    // Optionally implement a server-side handshake with the client here.
    // For example: read initial bytes, validate authentication token, etc.
    //
    // We'll skip that here and move straight to backend connection.

    let mut outbound = TcpStream::connect(backend_addr).await?;
    // now do full-duplex proxy with transform hooks
    proxy_apply_transforms(&mut inbound, &mut outbound).await?;
    Ok(())
}

/// Core proxy loop: reads from `a` and writes to `b`, and vice-versa.
/// Applies transform (deobfuscation/obfuscation) hooks to the data passing through.
async fn proxy_apply_transforms(a: &mut TcpStream, b: &mut TcpStream) -> Result<()> {
    // split both streams to operate concurrently.
    let (mut ar, mut aw) = a.split();
    let (mut br, mut bw) = b.split();

    // client -> backend task (deobfuscate incoming data and write plaintext to backend)
    let c_to_s = async {
        let mut buf = [0u8; 16 * 1024];
        loop {
            let n = ar.read(&mut buf).await?;
            if n == 0 {
                // EOF from client
                bw.shutdown().await.ok();
                break;
            }
            // server-side: transform incoming (obfuscated) bytes into underlying Tor bytes
            let plain = transform_incoming(&buf[..n]).await?;
            bw.write_all(&plain).await?;
        }
        Ok::<(), anyhow::Error>(())
    };

    // backend -> client task (obfuscate backend bytes before sending back)
    let s_to_c = async {
        let mut buf = [0u8; 16 * 1024];
        loop {
            let n = br.read(&mut buf).await?;
            if n == 0 {
                // EOF from backend
                aw.shutdown().await.ok();
                break;
            }
            // server-side: transform outgoing (plain Tor bytes) into obfuscated bytes
            let obf = transform_outgoing(&buf[..n]).await?;
            aw.write_all(&obf).await?;
        }
        Ok::<(), anyhow::Error>(())
    };

    // run both directions concurrently and return when both finish or any errors occur
    tokio::try_join!(c_to_s, s_to_c)?;
    Ok(())
}

/// Transform data arriving from client (obfuscated -> plain)
/// TODO: replace identity with your de-obfuscation logic (framing, decryption, etc).
async fn transform_incoming(data: &[u8]) -> Result<Vec<u8>> {
    // identity (no-op)
    Ok(data.to_vec())
}

/// Transform data going to client (plain -> obfuscated)
/// TODO: replace identity with your obfuscation logic (framing, encryption, mimicry).
async fn transform_outgoing(data: &[u8]) -> Result<Vec<u8>> {
    // identity (no-op)
    Ok(data.to_vec())
}
