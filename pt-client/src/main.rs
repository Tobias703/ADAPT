use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::env;
use std::sync::Arc;
use std::time::Duration;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // CLI: first arg is server addr (default 127.0.0.1:3030), second optional "obf" to match server
    let mut args = env::args().skip(1);
    let addr = args.next().unwrap_or_else(|| "127.0.0.1:3030".into());
    let use_obf = args.next().map(|s| s == "obf").unwrap_or(false);
    let key = Arc::new(b"devkey".to_vec());
    println!("PT client connecting to {}, obf={}", addr, use_obf);

    let mut sock = TcpStream::connect(&addr).await?;
    // Simple demo message
    let hello = "hello from client over PT (cleartext framing)".as_bytes();
    let payload = if use_obf { xor_bytes(hello, &key) } else { hello.to_vec() };
    write_msg(&mut sock, &payload).await?;
    println!("sent {} bytes", payload.len());

    // read reply with timeout
    let reply = tokio::time::timeout(Duration::from_secs(5), read_msg(&mut sock)).await?;
    let reply = reply?;
    let reply_plain = if use_obf { xor_bytes(&reply, &key) } else { reply };
    println!("reply ({} bytes): {}", reply_plain.len(), String::from_utf8_lossy(&reply_plain));

    Ok(())
}

async fn read_msg(sock: &mut TcpStream) -> anyhow::Result<Vec<u8>> {
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

fn xor_bytes(data: &[u8], key: &std::sync::Arc<Vec<u8>>) -> Vec<u8> {
    data.iter().enumerate().map(|(i, b)| b ^ key[i % key.len()]).collect()
}
