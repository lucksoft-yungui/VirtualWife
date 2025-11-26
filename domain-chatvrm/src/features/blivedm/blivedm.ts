// 获取当前环境变量，假设为PRODUCT_ENV
const environment = process.env.NODE_ENV;

// 定义基础URL
let baseUrl = "";
if (environment === "development") {
  baseUrl = ":8000";
} else if (environment === "production") {
  baseUrl = "/api";
} else {
  throw new Error("未知环境变量");
}


export async function connect(): Promise<WebSocket> {
    // 使用 host 以包含端口（如 8080），否则默认 80 端口会导致连接失败
    const host = window.location.host;
    const socket = new WebSocket(`ws://${host}${baseUrl}/ws/`);
    socket.onopen = () => {
        console.log('WebSocket connection established.');
        socket.send('connection success');
    };
    socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
        // 重新连接，每隔1秒尝试一次
        setTimeout(() => {
            console.log('Reconnecting...');
            connect(); // 重新调用connect()函数进行连接
        }, 1000);
    };
    return socket;
}
