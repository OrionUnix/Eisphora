const path = require('path'); // path is no longer strictly necessary for aliases, but can remain if used elsewhere

/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: 'http://127.0.0.1:8000',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET,OPTIONS,HEAD',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'X-Requested-With, Content-Type, Accept',
          },
        ],
      },
    ];
  },

};

