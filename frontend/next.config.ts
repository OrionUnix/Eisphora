/** @type {import('next').NextConfig} */
const nextConfig = {
    async headers() {
        return [
            {
                source: '/(.*)',
                headers: [
                    {
                        key: 'Access-Control-Allow-Origin',
                        value: 'http://localhost:8000',
                    },
                ],
            },
        ];
    },
};

module.exports = nextConfig;
