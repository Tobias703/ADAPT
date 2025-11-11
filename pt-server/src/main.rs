use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::env;
use std::sync::Arc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // simple CLI: first arg is bind addr (default 0.0.0.0:3030), second optional "obf" enables XOR obf
    let mut args = env::args().skip(1);
    let bind = args.next().unwrap_or_else(|| "0.0.0.0:3030".into());
    let use_obf = args.next().map(|s| s == "obf").unwrap_or(false);

    let key = Arc::new(b"devkey".to_vec()); // simple XOR key (example only)
    println!("PT server listening on {}, obf={}", bind, use_obf);

    let listener = TcpListener::bind(bind).await?;
    loop {
        let (sock, peer) = listener.accept().await?;
        let key = key.clone();
        tokio::spawn(async move {
            if let Err(e) = handle_connection(sock, peer.to_string(), use_obf, key).await {
                eprintln!("Connection {} error: {}", peer, e);
            }
        });
    }
}

async fn handle_connection(mut sock: TcpStream, peer: String, use_obf: bool, key: std::sync::Arc<Vec<u8>>) -> anyhow::Result<()> {
    println!("Accepted connection from {}", peer);

    // We'll loop: read messages from client and reply.
    loop {
        let msg = match read_msg(&mut sock).await {
            Ok(m) => m,
            Err(e) => {
                println!("{}: read_msg EOF or error: {}", peer, e);
                return Ok(());
            }
        };

        let payload = if use_obf { xor_bytes(&msg, &key) } else { msg };

        // Print as UTF-8 if possible
        match std::str::from_utf8(&payload) {
            Ok(s) => println!("{} -> received: {}", peer, s),
            Err(_) => println!("{} -> received ({} bytes, non-utf8)", peer, payload.len()),
        }

        // Reply
        let reply_text = format!("ack: received {} bytes", payload.len());
        let reply_bytes = if use_obf { xor_bytes(reply_text.as_bytes(), &key) } else { reply_text.into_bytes() };
        write_msg(&mut sock, &reply_bytes).await?;
    }
}

async fn read_msg(sock: &mut TcpStream) -> anyhow::Result<Vec<u8>> {
    // 4-byte big-endian length prefix
    let mut lenb = [0u8; 4];
    sock.read_exact(&mut lenb).await?;
    let len = u32::from_be_bytes(lenb) as usize;
    let mut buf = vec![0u8; len];
    sock.read_exact(&mut buf).await?;
    Ok(buf)
}

async fn write_msg(sock: &mut TcpStream, payload: &[u8]) -> anyhow::Result<()> {
    let len = (payload.len() as u32).to_be_bytes();
    sock.write_all(&len).await?;
    sock.write_all(payload).await?;
    Ok(())
}

fn xor_bytes(data: &[u8], key: &Vec<u8>) -> Vec<u8> {
    data.iter().enumerate().map(|(i, b)| b ^ key[i % key.len()]).collect()
}
